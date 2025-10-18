Below is a concrete, implementation-ready architecture for CarScout AI derived from your plan. It includes system context, components, event-driven flows, queue topology, core schemas, APIs, worker schedules, ML/LLM control, observability, security, deployment, and repo layout so you can start building immediately.
System context and core services Actors
Buyers via Telegram (public channel + user bot)
Admin operators (internal UI)
Marketplaces (Mobile.bg, Cars.bg, OLX, etc.)
Stripe Billing
OpenAI API
Object storage (R2/S3)
Managed Postgres and Redis
Proxy provider (optional)
Services
api: FastAPI app for public/internal APIs and Telegram webhook endpoints
worker-scrape: Scrapy + Playwright micro-scrapers
worker-normalize: normalization, brand/model mapping
worker-dedupe: duplicate detection (heuristics + embeddings + image hash)
worker-price: pricing model inference
worker-ai: risk classification and LLM summarization
worker-score: scoring + rank/filter + business rules
worker-notify: Telegram postings, user alerts
scheduler: Celery Beat schedules (scrapes, rescoring, validations)
telegram-bot: aiogram runner (optional; can be merged into api if using webhooks)
admin-ui: minimal internal admin panel (can be part of api)
infra: Nginx reverse proxy, metrics stack
Core data stores
Postgres (source of truth, with pgvector + pg_trgm)
Redis (Celery broker, cache, rate-limits, idempotency keys)
Object storage (R2/S3) for raw HTML snapshots and optional images
External integrations
Telegram Bot API
Stripe Billing
OpenAI gpt-4o-mini
Optional proxy networks
2. Event-driven pipeline and queues Canonical event flow
ingest.raw_saved → parsed.saved → normalized.saved → dedup.resolved → price.predicted → ai.evaluated → score.computed → approved → notify.channel | notify.user_alerts
Celery queues (Redis)
scrape.new_raw
parse.extract_fields
normalize.apply
dedupe.check
price.estimate
ai.classify
ai.llm_eval
score.rank_filter
notify.channel
notify.user
admin.rescore
housekeeping.validation
Event payload (minimal, used across tasks)
listing_id (UUID), source_id, site_ad_id, url
listing_version (int, increments on meaningful changes)
description_hash, image_hashes[0]
timestamps: first_seen_at, last_seen_at
normalized fields snapshot (brand_id, model_id, year, mileage_km, fuel, gearbox, body, price_bgn, region)
state flags: is_active, is_duplicate, duplicate_of
provenance: parsed_at, normalized_at, priced_at, ai_eval_at, scored_at, approved_at
Idempotency
Every task uses listing_id + listing_version as idempotency key in Redis with short TTL
Tasks are retryable; side effects wrapped in DB transactions
Dead-letter list in Redis for manual inspection
3. Database model (expanded) Conventions
UUID primary keys
created_at, updated_at on all core tables
Partition large append-only tables as needed (e.g., prices_history)
Sensitive data minimized; phone hashed
Core
sources(id, name, base_url, robots_cache JSONB, enabled, crawl_interval_s)
listings_raw(id, source_id, site_ad_id, url, raw_html_path, first_seen_at, last_seen_at, is_active, http_status, etag, last_modified, parse_errors)
listings_normalized(id, raw_id, brand_id, model_id, year int, mileage_km int, fuel, gearbox, body, price_bgn numeric, currency, region, title, description, features JSONB, description_hash, first_image_hash, listing_version int, is_duplicate bool, duplicate_of UUID null)
images(id, listing_id, url, object_key, hash, width, height, index)
sellers(id, phone_hash, name, site_profile_url, contact_count int, blacklist bool, notes)
prices_history(id, listing_id, price_bgn numeric, seen_at timestamptz)
comps_cache(listing_id, predicted_price_bgn numeric, discount_pct numeric, sample_size int, p50 numeric, p10 numeric, p90 numeric, features JSONB, computed_at, model_version)
evaluations(id, listing_id, flags JSONB, risk_level enum(low,med,high), llm_summary text, llm_confidence numeric, rule_confidence numeric, model_versions JSONB, evaluated_at)
scores(id, listing_id, score numeric, reasons JSONB, freshness_bonus numeric, liquidity numeric, risk_penalty numeric, final_state enum(draft,approved,rejected), scored_at)
channel_posts(listing_id, telegram_message_id, posted_at, channel, status)
brand_models(id, brand, model, aliases text[], locale, normalized_brand, normalized_model, active bool)
dedupe_signatures(id, listing_id, title_trgm text, title_minhash bytea, desc_minhash bytea, first_image_phash bigint, embeddings vector, created_at)
duplicates_log(id, listing_id, duplicate_of, method enum(heuristic,embedding,image), score numeric, decided_at)
Users, subscriptions, alerts
users(id, telegram_user_id unique, email unique null, role enum(user,admin), status, created_at)
plans(id, name enum(Free,Premium,Pro), limits JSONB, price_bgn)
subscriptions(id, user_id, plan_id, status enum(active,past_due,canceled), billing_provider enum(Stripe,Telegram), provider_customer_id, provider_sub_id, current_period_end, updated_at)
alerts(id, user_id, dsl_query text, normalized_filters JSONB, plan_required, created_at, active bool)
alert_matches(id, alert_id, listing_id, matched_at, delivered_at, delivery_status enum(pending,delivered,skipped,failed), reason)
reservations(id, listing_id, user_id, priority int, created_at, status enum(pending,claimed,canceled))
notifications_log(id, user_id, listing_id, type enum(channel,user_alert), sent_at, status, provider_message_id)
Indexes and extensions
Unique: (source_id, site_ad_id)
Btree: (brand_id, model_id, year), (price_bgn), (first_seen_at desc)
GIN: features, normalized_filters, flags
pg_trgm: title, description for fuzzy search
pgvector: dedupe_signatures.embeddings
Partial index: sellers(phone_hash) where blacklist = true
4. API surface (FastAPI) Public/Telegram
POST /telegram/webhook: aiogram update handler, verifies secret token
GET /healthz, /readiness
POST /webhooks/stripe: subscription lifecycle events
GET /v1/listings/{id}: read-only listing details (optional for web dashboard)
POST /v1/users/link-telegram: exchange code for telegram_user_id (optional)
Internal/admin
POST /admin/rescrape: {source_id, path or url, count}
POST /admin/re-evaluate: {listing_id[]}
POST /admin/blacklist/seller: {phone_hash | seller_id}
GET/POST /admin/brand-models: CRUD alias mappings
POST /admin/watches/test: {dsl_query} → normalized_filters + sample matches
Filtering/Ranking internal
POST /internal/filter-rank: {filters, top_k, dedupe=true} → {listings, reasons}
POST /internal/approve-for-channel: {listing_id}
Alerts DSL (examples)
“BMW X5 дизел <25000 2016+ <180000km автомат”
Grammar tokens: brand, model, fuel, price_bgn, year, mileage_km, gearbox, body, region
Operators: <, <=, >, >=, + suffix for lower bound on year, km suffix
Normalize to JSONB filters: {brand_id, model_id, price_bgn: {lte:25000}, year:{gte:2016}, mileage_km:{lte:180000}, fuel:‘diesel’, gearbox:‘auto’}
5. Scraping architecture Per-source micro-scrapers
Scrapy spiders per site for new/latest pages
scrapy-playwright for JS-heavy pages
Requests+lxml for simple endpoints
Store: listings_raw (raw_html_path → R2), parsed fields in listings_normalized (initial)
Respect robots.txt, ETag/Last-Modified, low concurrency
Scheduler
Celery Beat schedules per source every 1–3 minutes for latest pages
Parameters: last N pages, backoff if no changes, track last seen site_ad_id
Parsing output fields
brand, model, year, mileage_km, fuel, gearbox, body, price, currency, region, seller phone(s) (hashed), title, description, photos, link, site_ad_id
Anti-bot hygiene
Rotate UA, random jitter, per-domain concurrency=1–2, retry with backoff, proxy added only when blocked
6. Normalization and deduplication Normalization
brand_models mapping with aliases + Bulgarian spellings
fuel, gearbox, body standardized enumerations
currency conversion to BGN with daily FX rates
numeric cleanup for mileage and year
Deduplication
Heuristics: same phone_hash OR high title trigram similarity AND near-identical price/year/km within thresholds
Content hashes: MinHash of title+desc, dHash/pHash of first image
Embeddings: multilingual sentence-transformers or BGE; similarity threshold tuned; stored in pgvector
Resolution: set listings_normalized.is_duplicate=true and duplicate_of pointer; keep earliest/cleanest as canonical
7. Pricing model (non-LLM) Feature set
brand, model, year, mileage_km (log or linear), fuel, gearbox, body, region
Optional age/mileage interactions
Training
Nightly job per segment with minimum sample size
If sparse: robust median by segment + mileage slope via linear regression
Store model artifacts in R2; model_version tracked in comps_cache
Quantile regression for P10/P50/P90; fallback to empirical percentiles
Inference
price.estimate task: compute predicted_price, discount_pct, comp_sample_size, confidence; persist in comps_cache
8. AI layer (risk + explanation + scoring) Classifier (cheap first-pass)
Regex/keywords in BG: salvage/accident, “нов внос,” “реални километри,” “сервизна история,” “първи собственик,” urgent sale, cosmetic issues
Small multilingual model optional to refine flags
Output flags JSONB + rule_confidence
LLM escalation
Only when uncertain or when preliminary score suggests potential approval
Model: gpt-4o-mini
Prompt returns: risk_level, 2–3 reasons, buyer notes, confidence
Cache by description_hash; store in evaluations
Scoring (1–10)
Price advantage (0–5): from discount_pct and comps confidence
Risk penalty (0 to -4): from flags + LLM risk
Liquidity (+0–1): proxy from local supply or days-on-market if available
Freshness (+0–0.5)
Business rules can cap or boost
If score >= threshold and comp_sample_size/confidence pass → approved
9. Filtering, ranking, and diversity
Channel pipeline: score.desc, freshness.desc
Diversity: H-NSW-like suppression per brand-model so channel isn’t spammy; e.g., max K per brand/model per 6h
Blacklists: sellers, regions, keywords
Rate-limits: per hour posting caps; per-user alert caps by plan
10. Telegram integration Bots
Channel Poster Bot: consumes approved_listing queue; posts media groups with captions; inline buttons (Open, Save, Reserve)
User Bot: /start, /watch, /unwatch, /plan, /help; link subscription; manage reservations; confirm actions via inline keyboards
Delivery logic
Channel posts: idempotent by listing_id; edit message on price updates
Personal alerts: per alert match create notifications with plan-based delay (Free: +15–60 min, Premium: immediate)
Retries with backoff; store provider_message_id for edits/deletes
11. Subscriptions, payments, entitlements Stripe Billing
Checkout → webhook events (customer.created, subscription.updated, invoice.payment_succeeded/failed)
Update subscriptions table; enforce limits in matching engine
Entitlements per plan: watches count, alerts delay, daily caps, reservation priority
12. Observability and QA Logging
Structured JSON: service, request_id/correlation_id, listing_id, task_name, event, duration_ms, outcome
Centralize to Loki or ELK; Sentry for exceptions
Metrics (Prometheus)
Scrape: pages/min, new listings/min, HTTP error rates, blocked signals
Pipeline: queue depths, task durations, success/failure, dedupe rates
Model: pricing MAE/MedAE, quantile coverage, LLM utilization rate
Delivery: posts/min, alert latencies, per-plan delays
Dashboards and alerts
Queue backlogs, error rates, source-specific failures, model drift (e.g., price residuals)
Data quality jobs
Detect outliers (e.g., price_bgn beyond P99 + factor), unit mismatches, schema drift on sources
13. Security and compliance
Secrets via environment, managed in Vault/1Password; rotated
Telegram webhook secret token, optional IP allowlist
TLS everywhere; DB network policies; least-privileged DB roles
PII minimization: phone numbers hashed with stable salt; do not store raw
Rate-limit scraping; respect robots; pause switch per source
14. Deployment and scaling MVP (single VPS + managed DB/cache)
VPS: Nginx → FastAPI + uvicorn; Celery workers; Celery Beat; Scrapy spiders; Prometheus node exporter
Managed Postgres (Neon/Supabase) and Redis (Upstash/Redis Cloud)
R2/S3 for storage
Scale-out
Split workers by function: scraping, AI/ML, notifications
Dedicated headless-browser box for Playwright
Horizontal scale Celery workers; tune prefetch and concurrency
Consider Kubernetes later for HPA, job queues, resource isolation
Throughput sizing (initial)
10k new/updated ads/day, average pipeline latency < 2–5 minutes
Celery concurrency: scrape 4–8; normalize 4; dedupe 2–4; price 2; ai 2; score 2; notify 2
Redis rate limits for Telegram send to avoid flood
Backups and retention
Nightly Postgres snapshots; WAL archiving
Retain raw HTML 30–90 days; images first N per listing
PII hashes retained; no raw phone storage
15. Repository structure
apps/api: FastAPI app (routers for public/internal/admin, Telegram webhook)
apps/bot: aiogram handlers, message templates
workers/scrape: Scrapy projects per source, playwright helpers
workers/pipeline: tasks for normalize, dedupe, price, ai, score, notify
libs/domain: domain services, scoring, rules
libs/schemas: Pydantic models, event payloads
libs/ml: pricing training/inference, model registry client
infra/docker: docker-compose, Nginx config
infra/ci: GitHub Actions workflows
migrations: Alembic
configs: per-env settings
16. CI/CD
GitHub Actions:
Lint/format (ruff/black), mypy
Unit tests + integration (Postgres/Redis via services)
Build Docker images; push to registry
Run Alembic migrations on deploy
Canary deploy for workers; health checks; rollback on failure
17. Testing strategy
Unit: parsers per site (HTML fixtures), normalization rules, scoring math
Integration: pipeline E2E on synthetic listings; dedupe similarity thresholds
Contract tests: event payload schemas, API endpoints
Load tests: scraping rate, Telegram posting under caps
Offline ML validation: pricing backtests with holdout; quantile coverage
18. ML/LLM governance
Pricing model registry: model_version tagged; metrics logged; simple CSV/Parquet artifacts in R2
LLM caching by description_hash; TTL long; only recompute on change
Audit: store prompts and responses hashes, not raw prompts with PII
19. Detailed workflows (happy paths) New listing
Scrape → listings_raw saved + raw_html to R2
Parse → listings_normalized draft with parsed fields
Normalize → map brand/model, standardize enums, convert price to BGN
Dedupe → set is_duplicate/duplicate_of, or proceed
Price → comps_cache computed
AI → rule flags; LLM if needed; evaluations saved
Score → final score, reasons; if approved → to notify queues
Channel posting
worker-notify consumes approved listings
Check diversity, caps; compose carousel with first 5 images
Post to Telegram; save channel_posts
On price update: edit existing message
User alerts
Matching engine runs on new approved listings
For each alert: plan check, apply delay, enqueue notify.user
Send DM; log notifications; apply per-day caps
Stripe subscription update
Stripe webhook → verify signature → update subscriptions
Matching engine enforces new entitlements immediately
20. Initial thresholds and rules (tunable)
Dedupe thresholds: title trigram > 0.75 and price/year/km within 5–10%; or same phone_hash
Price scoring: discount 10–20% with high confidence maps to 3–5 points
Risk penalty: high → -3 to -4; medium → -1 to -2
Channel approval default: score >= 7.5 and comp_sample_size >= 30 with confidence >= 0.6
Free plan delay: 30 minutes; Premium: 0 minutes
This blueprint is ready to translate into code. If helpful, I can provide:
docker-compose service definitions and env variables
Pydantic schemas for events and tables
Example Celery task signatures and queue bindings
A minimal parser for Mobile.bg with tests
A first version of the pricing training notebook and inference module
