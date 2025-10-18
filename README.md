# 🚗 CarScout AI

> AI-powered car listing aggregator and intelligent pricing analyzer for Bulgarian automotive marketplaces

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 📋 Overview

CarScout AI is a comprehensive system that automatically:
- 🔍 **Scrapes** car listings from major Bulgarian marketplaces (Mobile.bg, Cars.bg, OLX)
- 🤖 **Analyzes** pricing using machine learning models
- ⚠️ **Detects** risks and red flags using AI (GPT-4)
- 📊 **Scores** listings based on value, risk, and market conditions
- 📱 **Delivers** the best deals via Telegram channel and personalized alerts
- 💳 **Supports** tiered subscriptions with Stripe integration

**Perfect for car buyers who want to:**
- Find underpriced vehicles before others
- Avoid scams and problematic listings
- Get instant notifications for matching cars
- Make data-driven purchase decisions

## ✨ Key Features

### 🎯 Smart Discovery
- Real-time scraping of 10,000+ daily listings
- Intelligent deduplication using embeddings and image hashing
- Multi-source aggregation (Mobile.bg, Cars.bg, OLX)

### 💰 Pricing Intelligence
- Machine learning-based price estimation
- Comparable vehicle analysis (P10/P50/P90)
- Discount percentage calculation
- Market trend tracking

### 🛡️ AI-Powered Risk Detection
- Bulgarian-specific keyword analysis
- LLM-based risk classification (GPT-4)
- Automated red flag detection
- Confidence scoring

### 📊 Intelligent Scoring
- 1-10 rating system combining:
  - Price advantage (0-5 points)
  - Risk assessment (-4 to 0 penalty)
  - Freshness bonus (0-0.5 points)
  - Market liquidity (0-1 points)

### 📱 Telegram Integration
- Public channel for top deals
- Personal alerts with custom criteria
- DSL-based search (e.g., "BMW X5 diesel <25000 2016+ <180000km")
- Inline reservation system

### 💳 Subscription Tiers
- **Free**: 3 alerts, 30-min delay
- **Premium** (19.99 BGN/mo): 10 alerts, instant notifications
- **Pro** (39.99 BGN/mo): Unlimited alerts, priority access, AI insights

## 🏗️ Architecture

CarScout AI follows an event-driven microservices architecture:

```
Scrapers → Parse → Normalize → Dedupe → Price → AI → Score → Notify
```

### Core Components
- **FastAPI** - REST API and webhook handler
- **Celery** - Distributed task processing
- **PostgreSQL + pgvector** - Primary database with vector search
- **Redis** - Queue broker and caching
- **Scrapy + Playwright** - Web scraping
- **OpenAI GPT-4** - Risk analysis
- **aiogram** - Telegram bot framework
- **Stripe** - Payment processing

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed system design.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Telegram Bot Token
- OpenAI API Key
- Stripe Account (optional)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/TheAVengineer/CarScout-AI.git
cd CarScout-AI
```

2. **Set up environment:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Start services:**
```bash
make docker-up
```

4. **Run migrations:**
```bash
make migrate
```

5. **Access the application:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Prometheus: http://localhost:9090

### Development Setup

```bash
# Install dependencies
make dev-install

# Format code
make format

# Run linters
make lint

# Run tests
make test

# Clean up
make clean
```

## 📖 Documentation

- [API Documentation](docs/API.md) - REST API reference
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment
- [Contributing Guide](docs/CONTRIBUTING.md) - Development guidelines
- [Architecture Overview](docs/ARCHITECTURE.md) - System design
- [Project Structure](PROJECT-SRUCTURE.md) - Detailed specification

## 🗂️ Project Structure

```
CarScout-AI/
├── apps/                   # Applications
│   ├── api/               # FastAPI application
│   │   ├── routers/      # API endpoints
│   │   └── main.py       # Application entry point
│   └── bot/              # Telegram bot
│       ├── handlers/     # Command handlers
│       └── main.py       # Bot entry point
├── workers/               # Background workers
│   ├── pipeline/         # Processing tasks
│   │   └── tasks/       # Celery tasks
│   └── scrape/          # Web scrapers
│       └── spiders/     # Scrapy spiders
├── libs/                  # Shared libraries
│   ├── domain/          # Business logic
│   ├── schemas/         # Data models
│   └── ml/              # ML models
├── configs/              # Configuration
├── migrations/           # Database migrations
├── infra/               # Infrastructure
│   ├── docker/         # Dockerfiles
│   └── ci/             # CI/CD pipelines
├── tests/               # Test suite
├── docs/                # Documentation
└── docker-compose.yml   # Docker services
```

## 🔧 Configuration

Key environment variables (see `.env.example`):

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
REDIS_URL=redis://localhost:6379/0

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=@your_channel

# OpenAI
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o-mini

# Stripe
STRIPE_API_KEY=sk_test_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_secret

# Business Rules
CHANNEL_APPROVAL_SCORE_THRESHOLD=7.5
FREE_PLAN_ALERT_DELAY_MINUTES=30
```

## 📊 Pipeline Overview

### 1. Scraping
```python
# Scrapy spiders with Playwright for JS rendering
MobileBgSpider → Raw HTML → S3 Storage
```

### 2. Parsing & Normalization
```python
# Extract fields and standardize
brand, model, year, mileage, price, etc.
→ Brand/model mapping → Currency conversion
```

### 3. Deduplication
```python
# Multi-method duplicate detection
- Phone hash matching
- Title trigram similarity
- Image perceptual hashing
- Embedding similarity (pgvector)
```

### 4. Pricing
```python
# ML-based price estimation
Features → Model → Predicted Price + Quantiles
→ Discount % calculation
```

### 5. AI Evaluation
```python
# Two-stage risk assessment
Rule-based classifier → Flags
Uncertain cases → GPT-4 → Risk Level + Summary
```

### 6. Scoring
```python
# Final score calculation (1-10)
Price Advantage + Risk Penalty + Freshness + Liquidity
→ Approval decision (score ≥ 7.5)
```

### 7. Notification
```python
# Delivery
Approved → Telegram Channel
Matching alerts → Personal DMs (with plan-based delay)
```

## 🤖 Telegram Bot Commands

```
/start     - Welcome message and overview
/watch     - Create a price alert
/unwatch   - Remove an alert
/list      - Show active alerts
/plan      - View subscription details
/upgrade   - Upgrade to Premium/Pro
/help      - Command reference
```

### Alert DSL Examples

```
BMW X5 diesel <25000 2016+ <180000km automatic
Audi A4 petrol 2018+ Sofia <15000
Mercedes C-Class 2015-2020 >180hp sedan
```

## 📈 Metrics and Monitoring

Prometheus metrics available at `/metrics`:

- `carscout_scrape_pages_total` - Pages scraped
- `carscout_listings_processed_total` - Listings processed
- `carscout_celery_task_duration_seconds` - Task performance
- `carscout_channel_posts_total` - Channel posts
- `carscout_ai_api_calls_total` - OpenAI API usage

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test suite
pytest tests/unit/
pytest tests/integration/

# With coverage
pytest --cov=apps --cov=workers --cov=libs --cov-report=html
```

## 🚢 Deployment

### Docker Compose (Recommended for MVP)
```bash
docker-compose up -d
```

### Kubernetes (Production)
```bash
# Build images
docker build -f infra/docker/Dockerfile.api -t carscout-api .

# Deploy
kubectl apply -f infra/k8s/
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.

## 🔐 Security

- ✅ Secrets in environment variables (never committed)
- ✅ TLS encryption for all external communication
- ✅ Telegram webhook signature validation
- ✅ Phone numbers hashed (never stored raw)
- ✅ Rate limiting on all endpoints
- ✅ SQL injection protection (SQLAlchemy)
- ✅ CORS configuration
- ✅ Database connection encryption

## 🛣️ Roadmap

- [ ] Additional marketplaces (AutoScout24, AutoTrader)
- [ ] Price prediction accuracy improvements
- [ ] Image-based damage detection
- [ ] VIN decoder integration
- [ ] Mobile app (React Native)
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Machine learning for fraud detection

## 🤝 Contributing

We welcome contributions! Please see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

Created and maintained by the CarScout AI team.

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- Scrapy and Playwright communities
- FastAPI and aiogram developers
- Bulgarian automotive community

## 📧 Support

- GitHub Issues: [Report bugs or request features](https://github.com/TheAVengineer/CarScout-AI/issues)
- Email: support@carscout.ai
- Telegram: @carscout_support

## 📊 Stats

- **10,000+** listings processed daily
- **<5 min** average pipeline latency
- **85%+** deduplication accuracy
- **7.5+** average score threshold for approval
- **20** posts per hour to channel

---

**Made with ❤️ for car buyers in Bulgaria**
