# CarScout AI - Project Structure Summary

## Overview
This document provides a quick reference to the complete project structure.

## Statistics
- **41** Python files
- **4** Documentation files
- **3** Dockerfiles
- **1** Docker Compose file
- **Multiple** configuration files

## Directory Tree

```
CarScout-AI/
│
├── 📄 Core Files
│   ├── README.md                  # Main project documentation
│   ├── LICENSE                    # MIT license
│   ├── CHANGELOG.md              # Version history
│   ├── PROJECT-SRUCTURE.md       # Detailed architecture spec
│   ├── pyproject.toml            # Python project config
│   ├── alembic.ini               # Database migration config
│   ├── docker-compose.yml        # Docker services orchestration
│   ├── Makefile                  # Development commands
│   ├── .env.example              # Environment template
│   ├── .gitignore               # Git ignore rules
│   └── quickstart.sh            # Quick start script
│
├── 🚀 Applications (apps/)
│   ├── api/                      # FastAPI REST API
│   │   ├── main.py              # Application entry point
│   │   └── routers/             # API endpoints
│   │       ├── telegram.py      # Telegram webhook
│   │       ├── admin.py         # Admin endpoints
│   │       ├── internal.py      # Internal API
│   │       └── public.py        # Public API
│   │
│   └── bot/                      # Telegram Bot
│       ├── main.py              # Bot entry point
│       └── handlers/            # Command handlers
│           ├── start.py         # /start, /help
│           ├── watch.py         # /watch, /unwatch
│           └── plan.py          # /plan, /upgrade
│
├── ⚙️ Workers (workers/)
│   ├── pipeline/                 # Processing workers
│   │   ├── celery_app.py       # Celery configuration
│   │   └── tasks/              # Task definitions
│   │       ├── parse.py        # HTML parsing
│   │       ├── normalize.py    # Data normalization
│   │       ├── dedupe.py       # Duplicate detection
│   │       ├── price.py        # Price estimation
│   │       ├── ai.py           # AI evaluation
│   │       ├── score.py        # Scoring
│   │       └── notify.py       # Notifications
│   │
│   └── scrape/                   # Web scrapers
│       └── spiders/             # Scrapy spiders
│           └── mobile_bg.py    # Mobile.bg spider
│
├── 📚 Libraries (libs/)
│   ├── domain/                   # Business logic
│   │   └── scoring.py          # Scoring engine
│   │
│   ├── schemas/                  # Data models
│   │   └── events.py           # Event schemas
│   │
│   └── ml/                       # Machine learning
│       └── pricing.py          # Pricing model
│
├── ⚙️ Configuration (configs/)
│   └── settings.py              # Application settings
│
├── 🗄️ Migrations (migrations/)
│   ├── env.py                   # Alembic environment
│   ├── script.py.mako          # Migration template
│   └── versions/               # Migration files
│
├── 🏗️ Infrastructure (infra/)
│   ├── docker/                   # Docker files
│   │   ├── Dockerfile.api      # API image
│   │   ├── Dockerfile.bot      # Bot image
│   │   ├── Dockerfile.worker   # Worker image
│   │   ├── init-db.sql         # Database init
│   │   └── prometheus.yml      # Metrics config
│   │
│   └── ci/                       # CI/CD
│       └── github-actions.yml  # GitHub Actions
│
├── 📖 Documentation (docs/)
│   ├── API.md                   # API reference
│   ├── ARCHITECTURE.md          # System design
│   ├── DEPLOYMENT.md           # Deployment guide
│   └── CONTRIBUTING.md         # Contribution guide
│
└── 🧪 Tests (tests/)
    ├── conftest.py             # Pytest configuration
    ├── unit/                   # Unit tests
    │   └── test_scoring.py    # Scoring tests
    │
    └── integration/            # Integration tests
```

## Key Components

### API Service (apps/api/)
- **FastAPI** web framework
- RESTful endpoints for public, internal, and admin use
- Telegram webhook handler
- Prometheus metrics
- Health checks

### Bot Service (apps/bot/)
- **aiogram** Telegram bot framework
- User command handlers
- Interactive keyboards
- Alert management

### Pipeline Workers (workers/pipeline/)
- **Celery** distributed task queue
- 7 task types: parse, normalize, dedupe, price, ai, score, notify
- Queue-based processing
- Retry logic and error handling

### Scrapers (workers/scrape/)
- **Scrapy** web scraping framework
- **Playwright** for JavaScript rendering
- Per-source spider implementations
- Rate limiting and robots.txt compliance

### Shared Libraries (libs/)
- **domain/**: Business logic (scoring engine)
- **schemas/**: Pydantic data models
- **ml/**: Machine learning models (pricing)

### Configuration (configs/)
- Environment-based settings
- Pydantic validation
- Secret management

### Infrastructure (infra/)
- Docker containerization
- CI/CD pipelines
- Monitoring setup

## Getting Started

1. **Quick Start:**
   ```bash
   ./quickstart.sh
   ```

2. **Manual Setup:**
   ```bash
   make dev-install
   make docker-up
   make migrate
   ```

3. **Run Tests:**
   ```bash
   make test
   ```

4. **View Documentation:**
   - Main: `README.md`
   - API: `docs/API.md`
   - Deploy: `docs/DEPLOYMENT.md`

## Development Workflow

1. **Create feature branch**
2. **Write code with tests**
3. **Format code:** `make format`
4. **Run linters:** `make lint`
5. **Run tests:** `make test`
6. **Submit PR**

## Services

When running with Docker Compose:

| Service | Port | Description |
|---------|------|-------------|
| API | 8000 | REST API |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache/Queue |
| Prometheus | 9090 | Metrics |

## Environment Variables

See `.env.example` for all configuration options. Key variables:
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `TELEGRAM_BOT_TOKEN` - Bot authentication
- `OPENAI_API_KEY` - AI features
- `STRIPE_API_KEY` - Payment processing

## Next Steps

1. Configure `.env` with your credentials
2. Start services with `docker-compose up`
3. Access API docs at http://localhost:8000/docs
4. Read `docs/ARCHITECTURE.md` for system design
5. Check `docs/CONTRIBUTING.md` for development guidelines

---

For questions or issues, please see the [README.md](README.md) or open an issue on GitHub.
