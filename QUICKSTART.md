# 🚀 Quick Start - CarScout AI

## ✅ Fixed Issues

1. **Scripts now use virtual environment** - All shebang lines updated to `.venv/bin/python3`
2. **Database connection working** - Status script shows real counts
3. **System is running** - Celery workers (10), Beat scheduler, Telegram bot all active

---

## 📊 Current Status

```
Raw Listings: 31
Normalized: 6
Scored: 6
```

**What this means**: You have 31 scraped listings, but only 6 have been processed through the pipeline. The parse task needs completion to process the remaining 25.

---

## 🎯 Next Steps (The Right Workflow)

### Step 1: Seed the Database (Run Once)

This creates your **baseline data** for price comparisons:

```bash
# Run the seeding script
.venv/bin/python3 scripts/seed_database.py
```

**What it does:**
- Scrapes 300 listings (30 per brand × 10 brands)
- Takes 5-7 minutes
- Creates market baseline for price comparisons
- Staggered execution (avoids rate limiting)

**Expected result:**
```
Raw Listings: ~330 (31 existing + 300 new)
```

---

### Step 2: Complete the Parse Task

**File**: `workers/pipeline/tasks/parse.py`

**Current issue**: Lines 48-82 have placeholder code that needs replacement

**What needs to happen:**
1. Extract data from `raw_html` field using BeautifulSoup
2. Map Mobile.bg HTML structure to fields
3. Remove placeholder code
4. Wire parsed data to normalize task

**The Mobile.bg parser is DONE** (lines 136-256), it just needs to be called instead of the placeholder.

---

### Step 3: Test the Complete Pipeline

After fixing parse task:

```bash
# Trigger small test scrape
.venv/bin/python3 scripts/trigger_scrape.py
# Choose option 1, enter "BMW", max 5 items

# Watch processing in real-time
tail -f logs/celery-worker.log
```

---

### Step 4: Start Automated System

System is already running! Verify with:

```bash
.venv/bin/python3 scripts/status.py
```

**Automatic schedule (already active):**
- **Every 2 hours**: Scrape 300 listings → Process → Post top deals
- **Every 5 minutes**: Process any pending listings
- **Every hour**: Rescore existing listings
- **Daily 3 AM**: Cleanup

---

## 🔧 Useful Commands

### Check system status:
```bash
.venv/bin/python3 scripts/status.py
```

### Trigger manual scrape:
```bash
.venv/bin/python3 scripts/trigger_scrape.py
```

### Monitor live activity:
```bash
tail -f logs/celery-worker.log
```

### Check database counts:
```bash
.venv/bin/python3 -c "
from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw, ListingNormalized, Score
session = get_sync_session()
print(f'Raw: {session.query(ListingRaw).count()}')
print(f'Normalized: {session.query(ListingNormalized).count()}')
print(f'Scored: {session.query(Score).count()}')
"
```

---

## 📁 Important Documentation

- **WORKFLOW.md** - Complete algorithm explanation
- **SYSTEM-STATUS.md** - Full system documentation
- **QUICKSTART-WORKERS.md** - Celery worker details
- **AGENTS.md** - Development roadmap (95% complete)

---

## 🏆 Summary

**System is 95% complete!** Just need to:
1. Run seed script (build baseline)
2. Fix parse task (remove placeholder)
3. Test pipeline (5 BMW listings)
4. Watch deals appear in Telegram channel! 🚀
