# Architecture Overview

## System Architecture

CarScout AI is an event-driven, microservices-based system for aggregating, analyzing, and ranking car listings from Bulgarian automotive marketplaces.

### High-Level Components

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│ Marketplaces│─────▶│   Scrapers   │─────▶│  PostgreSQL │
└─────────────┘      └──────────────┘      └─────────────┘
                            │                      │
                            ▼                      ▼
                     ┌──────────────┐      ┌─────────────┐
                     │ Celery Queue │◀────▶│   Workers   │
                     └──────────────┘      └─────────────┘
                            │                      │
                            ▼                      ▼
                     ┌──────────────┐      ┌─────────────┐
                     │  FastAPI     │◀────▶│  Telegram   │
                     └──────────────┘      │    Bot      │
                                           └─────────────┘
                                                  │
                                                  ▼
                                           ┌─────────────┐
                                           │    Users    │
                                           └─────────────┘
```

## Data Flow

### Listing Ingestion Pipeline

1. **Scraping** - Scrapy spiders collect raw HTML
2. **Parsing** - Extract structured fields
3. **Normalization** - Standardize brands, models, units
4. **Deduplication** - Detect and mark duplicates
5. **Pricing** - Estimate market value
6. **AI Evaluation** - Risk classification + LLM insights
7. **Scoring** - Calculate final score (1-10)
8. **Approval** - Filter for channel posting
9. **Notification** - Post to channel + user alerts

### Event Flow

```
scrape → parse → normalize → dedupe → price → ai → score → notify
```

Each stage is a Celery task with its own queue and retry logic.

## Core Services

### API Service
- FastAPI application
- REST endpoints (public, internal, admin)
- Telegram webhook handler
- Health checks and metrics

### Bot Service
- aiogram-based Telegram bot
- User commands (/watch, /plan, /help)
- Inline keyboards and callbacks
- User state management

### Worker Services
- **worker-scrape** - Scraping tasks
- **worker-pipeline** - Processing tasks
- **worker-notify** - Notification tasks
- **scheduler** - Celery Beat for cron jobs

## Data Stores

### PostgreSQL
Primary database with:
- `pgvector` for embeddings
- `pg_trgm` for fuzzy text search
- Full schema in PROJECT-STRUCTURE.md

Key tables:
- `listings_raw` - Raw scraped data
- `listings_normalized` - Processed listings
- `scores` - Final scores and reasons
- `alerts` - User watch criteria
- `subscriptions` - Billing and plans

### Redis
Used for:
- Celery broker and results
- Rate limiting
- Caching
- Idempotency keys

### S3/R2
Object storage for:
- Raw HTML snapshots
- Listing images (optional)
- ML model artifacts

## Technology Stack

### Backend
- **Python 3.11+**
- **FastAPI** - Async web framework
- **Celery** - Distributed task queue
- **SQLAlchemy** - ORM
- **Alembic** - Migrations
- **Pydantic** - Data validation

### Scraping
- **Scrapy** - Web scraping framework
- **Playwright** - Browser automation
- **lxml** - HTML parsing

### AI/ML
- **OpenAI API** - LLM for risk evaluation
- **scikit-learn** - Pricing models
- **sentence-transformers** - Embeddings
- **pandas/numpy** - Data processing

### Messaging
- **aiogram** - Telegram Bot framework
- **Telegram Bot API** - User interaction

### Infrastructure
- **Docker** - Containerization
- **PostgreSQL 16** - Database
- **Redis 7** - Cache and queue
- **Prometheus** - Metrics
- **Nginx** - Reverse proxy

## Queues and Workers

### Celery Queues
- `scrape.new_raw` - Scraping jobs
- `parse.extract_fields` - HTML parsing
- `normalize.apply` - Normalization
- `dedupe.check` - Deduplication
- `price.estimate` - Pricing
- `ai.classify` - Risk classification
- `ai.llm_eval` - LLM evaluation
- `score.rank_filter` - Scoring
- `notify.channel` - Channel posts
- `notify.user` - User alerts

### Worker Concurrency
- Scraping: 4-8 workers
- Pipeline: 4 workers
- Notify: 2 workers (rate limited)

## Deduplication Strategy

Three-layer approach:

1. **Heuristics**
   - Same phone hash
   - High title similarity + similar price/year/km

2. **Content Hashing**
   - MinHash for text similarity
   - pHash/dHash for images

3. **Embeddings**
   - Multilingual sentence embeddings
   - pgvector similarity search
   - Threshold: 0.85

## Pricing Model

### Feature Engineering
- Brand, model, year, mileage
- Fuel type, gearbox, body style
- Region
- Age and mileage interactions

### Training
- Nightly per-segment training
- Quantile regression for P10/P50/P90
- Minimum sample size requirements
- Model versioning in S3

### Inference
- Cached predictions in `comps_cache`
- Discount percentage calculation
- Confidence scoring

## AI Risk Classification

### Rule-Based Classifier
Bulgarian keyword detection:
- Accident/salvage terms
- "First owner" claims
- Service history mentions
- Urgency indicators

### LLM Escalation
- Triggered for uncertain cases
- gpt-4o-mini model
- Cached by description_hash
- Returns risk_level + summary

## Scoring Algorithm

Score = Price Advantage + Risk Penalty + Freshness + Liquidity

- **Price Advantage** (0-5): Based on discount %
- **Risk Penalty** (0 to -4): From AI evaluation
- **Freshness** (0-0.5): Recent listings bonus
- **Liquidity** (0-1): Market demand indicator

**Approval Criteria:**
- Score ≥ 7.5
- Comp sample size ≥ 30
- Comp confidence ≥ 0.6

## User Subscription Tiers

### Free
- 3 price alerts
- 30-minute delay
- Channel access

### Premium (19.99 BGN/month)
- 10 price alerts
- Instant notifications
- Priority reservations

### Pro (39.99 BGN/month)
- Unlimited alerts
- Instant notifications
- Highest priority
- Direct seller contacts
- Custom AI insights

## Monitoring and Observability

### Metrics
- Scrape rates and errors
- Pipeline throughput
- Task durations
- Queue depths
- Price prediction accuracy
- User engagement

### Logging
- Structured JSON logs
- Request/correlation IDs
- Error tracking with Sentry
- Centralized log aggregation

### Alerts
- Queue backlogs > threshold
- Error rates > 5%
- Database connection issues
- API latency > 1s

## Security

- Secrets in environment variables
- TLS everywhere
- Telegram webhook signature validation
- Rate limiting per endpoint
- Phone number hashing
- PII minimization
- Database connection encryption

## Scalability

### Current Capacity
- 10k listings/day
- <5 minute pipeline latency
- 20 channel posts/hour

### Scaling Strategy
- Horizontal worker scaling
- Celery concurrency tuning
- Database connection pooling
- Redis clustering
- CDN for images
- Kubernetes for orchestration
