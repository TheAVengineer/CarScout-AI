# Changelog

All notable changes to CarScout AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- ✅ Complete project structure with microservices architecture (24 directories, 50+ files)
- ✅ FastAPI REST API with authentication, webhooks, and OpenAPI documentation
- ✅ Telegram bot with aiogram 3.x framework
- ✅ Celery-based distributed task processing with 8 specialized queues
- ✅ PostgreSQL database with 18 tables and comprehensive relationships
- ✅ pgvector extension for embedding-based similarity search
- ✅ pg_trgm extension for fuzzy text matching
- ✅ Alembic database migration system with initial schema
- ✅ Mobile.bg web scraper with Playwright support for JavaScript rendering
- ✅ Scraper pipeline for database persistence and task chaining
- ✅ Brand/model normalization with fuzzy matching and caching
- ✅ Field normalization for fuel, gearbox, body, mileage, year, currency
- ✅ Seeding function for 17 common Bulgarian car models
- ✅ AI-powered risk evaluation with two-stage classification
- ✅ Rule-based risk classifier with 75+ Bulgarian keywords
- ✅ OpenAI GPT-4o-mini integration for uncertain cases
- ✅ Telegram notification system with rich message formatting
- ✅ Media group support (up to 5 images per post)
- ✅ Inline keyboards with action buttons
- ✅ Rate limiting (20 posts/hour to channel)
- ✅ Subscription plans: Free, Premium ($19.99), Pro ($39.99)
- ✅ Docker Compose orchestration for 9 services
- ✅ Prometheus metrics and monitoring endpoints
- ✅ GitHub Actions CI/CD pipeline
- ✅ Development setup script (`scripts/dev_setup.sh`)
- ✅ Database seeding script (`scripts/seed_database.py`)
- ✅ System verification tests (`scripts/test_setup.py`)
- ✅ Comprehensive documentation:
  - `README.md` - Quick start and overview
  - `docs/API.md` - REST API reference
  - `docs/ARCHITECTURE.md` - System design
  - `docs/DEPLOYMENT.md` - Production deployment
  - `docs/CONTRIBUTING.md` - Development guidelines
  - `PROJECT-STRUCTURE.md` - Detailed specification

### Database Schema (18 Tables)
- `source` - Marketplace sources (Mobile.bg, Cars.bg, OLX)
- `listing_raw` - Raw scraped HTML and metadata
- `listing_normalized` - Cleaned and standardized listings
- `brand_model` - Brand/model normalization mappings with fuzzy matching
- `image` - Listing images with S3 URLs and metadata
- `seller` - Seller profiles with hashed phone numbers
- `price_history` - Historical price tracking
- `comp_cache` - Cached comparable vehicles for pricing
- `evaluation` - AI risk assessments with confidence scores
- `score` - Final listing scores (1-10 scale)
- `user` - Telegram users with plan associations
- `plan` - Subscription tiers with limits
- `subscription` - Active subscriptions with Stripe integration
- `alert` - User price alerts with DSL queries
- `alert_match` - Matched alerts to listings
- `channel_post` - Posted Telegram messages (idempotency)
- `dedupe_signature` - Deduplication signatures (phone, text, image, embedding)
- `duplicate_log` - Duplicate listing audit trail

### Pipeline Tasks (Celery)
- ✅ `normalize_listing` - Standardize brand/model and fields
- ✅ `classify_risk` - Rule-based risk detection
- ✅ `llm_evaluate` - GPT-4 risk analysis for uncertain cases
- ✅ `post_to_channel` - Post approved listings to Telegram
- ✅ `send_user_alert` - Send personalized alerts to users
- 🚧 `parse_listing` - Extract structured data from HTML (TODO)
- 🚧 `deduplicate_listing` - Multi-method duplicate detection (TODO)
- 🚧 `estimate_price` - ML-based price prediction (TODO)
- 🚧 `calculate_score` - Final score calculation (TODO)

### API Endpoints
- `/telegram/webhook` - Telegram bot webhook handler
- `/stripe/webhook` - Stripe payment webhook
- `/internal/stats` - System statistics and health
- `/public/listings` - Public listing search
- `/admin/sources` - Source management CRUD
- `/admin/metrics` - Prometheus metrics

### Features Implemented
- Real-time scraping with configurable intervals
- HTML storage in S3 for auditing
- Phone number hashing for privacy
- Two-stage AI evaluation (rules first, LLM for uncertain)
- LLM response caching based on description hash
- Telegram media groups with inline keyboards
- Channel posting with duplicate prevention
- Alert matching with plan-based delays
- Structured logging with JSON output
- Comprehensive error handling with Celery retry logic
- Database session management (async + sync)
- Migration system with schema versioning

### Configuration Files
- `.env.example` - Environment template
- `docker-compose.yml` - Service orchestration
- `pyproject.toml` - Python project configuration
- `Makefile` - Development commands
- `.gitignore` - Git exclusions
- `prometheus.yml` - Metrics configuration
- `alembic.ini` - Migration configuration
- `scrapy.cfg` - Scraper configuration

### Documentation Structure
```
docs/
├── API.md           # REST API reference (30+ endpoints)
├── ARCHITECTURE.md  # System design and data flow
├── DEPLOYMENT.md    # Production deployment guide
└── CONTRIBUTING.md  # Development guidelines
```

### Pending Implementation
- 📝 Parse task (extract structured data from raw HTML)
- 📝 Deduplication logic (text similarity, image hashing, embeddings)
- 📝 ML pricing model (training and inference)
- 📝 Score calculation (wire up ScoringEngine)
- 📝 Alert matching engine (DSL parser and matcher)
- 📝 Additional scrapers (Cars.bg, OLX)
- 📝 Image-based duplicate detection (pHash)
- 📝 Embedding generation (sentence-transformers)
- 📝 Price model training pipeline
- 📝 S3 integration for HTML storage
- 📝 Stripe payment webhooks
- 📝 Advanced analytics dashboard
- 📝 Unit and integration tests

## [0.1.0] - 2024-01-XX

### Added
- Initial release
- Core scraping functionality
- Basic pricing analysis
- AI risk detection
- Telegram notifications
- Subscription management
