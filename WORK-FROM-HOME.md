# 📋 Quick Reference - Working from Another PC

**Last Updated**: October 21, 2025  
**For**: Resuming CarScout AI development on a different machine

---

## 🎯 What's Done

✅ **All 7 pipeline stages are working and validated**:
1. Parse (extract data from HTML)
2. Normalize (standardize fields)
3. Dedupe (detect duplicates)
4. Price (estimate market value)
5. Risk (classify seller risk)
6. LLM (AI quality evaluation)
7. Score (calculate final rating)

✅ **6 critical bugs fixed**:
- Parse → Normalize ID passing
- Parse images field handling
- Dedupe field name mismatches
- Decimal type multiplication
- DedupeSignature creation
- SQL table names

---

## 🚀 Quick Start Commands

### 1. Clone & Setup (First Time on New PC)

```bash
git clone https://github.com/TheAVengineer/CarScout-AI.git
cd CarScout-AI

# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# Start infrastructure
docker-compose up -d postgres redis
alembic upgrade head
python scripts/seed_database.py
```

### 2. Run Pipeline Test (Any Day)

**Terminal 1** (Worker - keep open):
```powershell
cd C:\CarScout-AI
.\venv\Scripts\Activate.ps1
.\venv\Scripts\celery.exe -A workers.pipeline.celery_app worker --loglevel=info --pool=solo
```

**Terminal 2** (Tests):
```powershell
cd C:\CarScout-AI
.\venv\Scripts\Activate.ps1

# Trigger pipeline
.\venv\Scripts\python.exe -c "from workers.pipeline.tasks.parse import parse_listing; from libs.domain.database import get_sync_session; from libs.domain.models import ListingRaw; session = get_sync_session().__enter__(); listings = session.query(ListingRaw).filter(ListingRaw.parsed_data.isnot(None)).limit(6).all(); [parse_listing.delay(str(r.id)) for r in listings]; print(f'Triggered {len(listings)} parse tasks')"

# Wait 30 seconds, then check results
.\venv\Scripts\python.exe -c "from libs.domain.database import get_sync_session; from libs.domain.models import Score; session = get_sync_session().__enter__(); print(f'Total Scores: {session.query(Score).count()}')"
```

---

## 📚 Key Documents

Read these first when resuming work:

1. **[PIPELINE-DEBUG.md](PIPELINE-DEBUG.md)** ⭐ START HERE
   - All bug fixes explained
   - Step-by-step how to run pipeline on Windows
   - Common issues and solutions
   - Data quality notes

2. **[README.md](README.md)** - Project overview

3. **[AGENTS.md](AGENTS.md)** - All remaining tasks to reach 100%

4. **[STATUS.md](STATUS.md)** - Current completion status

5. **[TESTING.md](TESTING.md)** - Testing procedures

---

## 🐛 Quick Troubleshooting

### Worker Won't Start
```powershell
# Kill stuck processes
Get-Process python* | Stop-Process -Force

# Clear cache
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# Restart Docker
docker-compose restart postgres redis
```

### No Scores Generated
- Check worker is running (separate window)
- Verify PostgreSQL and Redis are running
- Wait 30+ seconds for pipeline completion
- Current data quality issue: scores will be 1.0 (rejected) due to missing price/brand/model

### Database Connection Error
```powershell
docker-compose up -d postgres redis
docker ps  # Verify running
```

---

## 🎯 Next Priority Tasks

According to **[AGENTS.md](AGENTS.md)**:

1. **Fix Spider Data Extraction** (HIGH PRIORITY)
   - Update Mobile.bg spider to extract price
   - Map Bulgarian brand/model names to IDs
   - Extract body type, region fields
   - File: `workers/scrape/spiders/mobile_bg.py`

2. **Add Cars.bg Spider** (HIGH PRIORITY)
   - Create new spider for Cars.bg
   - File: `workers/scrape/spiders/cars_bg.py`

3. **Complete Stripe Webhooks** (CRITICAL)
   - Handle payment events
   - File: `apps/api/routers/telegram.py`

See [AGENTS.md](AGENTS.md) for complete task breakdown.

---

## 💾 Important Files Modified (October 2025)

All fixes are committed. Key files changed:

- `workers/pipeline/tasks/parse.py` (lines 261, 299-302)
- `workers/pipeline/tasks/dedupe.py` (lines 6, 31-45, 74-76, 95-105, 215-221)
- `PIPELINE-DEBUG.md` (NEW - comprehensive debugging guide)
- `README.md` (updated with pipeline status)

---

## 🔑 Environment Variables Needed

Make sure `.env` file has:

```env
# Database
DATABASE_URL=postgresql://carscout:password@localhost:5432/carscout
POSTGRES_USER=carscout
POSTGRES_PASSWORD=your_password
POSTGRES_DB=carscout

# Redis
REDIS_URL=redis://localhost:6379/1
REDIS_RESULT_URL=redis://localhost:6379/2

# Optional (for full functionality)
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHANNEL_ID=@your_channel
STRIPE_SECRET_KEY=sk_test_...
```

---

## ✅ Validation Checklist

Before starting new work, verify:

- [ ] PostgreSQL running (`docker ps`)
- [ ] Redis running (`docker ps`)
- [ ] Virtual environment activated
- [ ] Worker starts without errors
- [ ] Can query database (run test command)
- [ ] All 11 Celery tasks loaded

**Test command**:
```powershell
.\venv\Scripts\python.exe -c "from libs.domain.database import get_sync_session; session = get_sync_session().__enter__(); print('Database connected!')"
```

---

## 📞 Questions?

- **Pipeline Issues**: See [PIPELINE-DEBUG.md](PIPELINE-DEBUG.md)
- **Setup Issues**: See [QUICK-START.md](QUICK-START.md)
- **Testing**: See [TESTING.md](TESTING.md)
- **Architecture**: See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

**Good luck! The pipeline is ready for production-level data.** 🚀
