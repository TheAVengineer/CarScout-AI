# Testing Quick Reference

## 🚀 Quick Start

```bash
# Run all tests
./scripts/run_tests.sh
```

## 📝 Individual Tests

### 1. Setup Test
```bash
python scripts/test_setup.py
```
**Tests**: DB connection, seeds, migrations

### 2. Pipeline Test
```bash
python scripts/test_pipeline.py
```
**Tests**: Parse → Normalize → Dedupe → Price → AI → Score

### 3. Alert Matcher Test
```bash
python scripts/test_alert_matcher.py
```
**Tests**: DSL parser, matching logic, rate limiting

### 4. Real Data Test
```bash
docker-compose exec worker scrapy crawl mobile_bg -a pages=1
```
**Tests**: Scraping, full pipeline with live data

## 🔍 Monitoring

### Flower (Task Monitor)
```bash
open http://localhost:5555
```

### Database Queries
```bash
# Connect to DB
docker-compose exec db psql -U carscout_user -d carscout_db

# Count listings
SELECT COUNT(*) FROM listing_normalized;

# Check recent scores
SELECT ln.normalized_brand, ln.normalized_model, s.total_score, s.state
FROM score s
JOIN listing_normalized ln ON s.listing_id = ln.id
ORDER BY s.created_at DESC
LIMIT 10;

# Check duplicates
SELECT COUNT(*) FROM listing_normalized WHERE is_duplicate = true;
```

### Logs
```bash
# All logs
docker-compose logs -f

# Worker only
docker-compose logs -f worker

# API only
docker-compose logs -f api
```

## ⚡ Common Commands

### Services
```bash
# Start all
docker-compose up -d

# Stop all
docker-compose down

# Restart
docker-compose restart

# View status
docker-compose ps
```

### Database
```bash
# Run migrations
alembic upgrade head

# Seed data
python scripts/seed_database.py

# Reset database (⚠️ deletes all data)
docker-compose down -v
docker-compose up -d db
alembic upgrade head
python scripts/seed_database.py
```

### Scraping
```bash
# Mobile.bg (1 page)
docker-compose exec worker scrapy crawl mobile_bg -a pages=1

# Mobile.bg (10 pages)
docker-compose exec worker scrapy crawl mobile_bg -a pages=10

# All sources
docker-compose exec worker scrapy crawl mobile_bg -a pages=5
docker-compose exec worker scrapy crawl cars_bg -a pages=5
docker-compose exec worker scrapy crawl olx -a pages=5
```

## 🐛 Debugging

### Check Task Status
```bash
# In Flower: http://localhost:5555
# Or via Python:
from workers.pipeline.celery_app import celery_app
celery_app.control.inspect().active()
```

### Check Redis Queue
```bash
docker-compose exec redis redis-cli
> LLEN celery
> KEYS *
```

### Check Celery Workers
```bash
docker-compose exec worker celery -A workers.pipeline.celery_app inspect active
docker-compose exec worker celery -A workers.pipeline.celery_app inspect stats
```

## 📊 Expected Results

### test_setup.py
```
✅ Database Connection
✅ Sources (3 found)
✅ Plans (Free, Premium, Pro)
✅ Brand/Model Mappings (17+ mappings)
✅ User Creation
✅ Normalization
✅ Risk Evaluation
🎉 All tests passed!
```

### test_pipeline.py
```
✅ Parse complete
✅ Normalize complete
✅ Dedupe complete
⚠️  Price complete (may fail if no comparables)
✅ AI Risk complete
✅ Score complete
🎉 Pipeline test PASSED!
```

### test_alert_matcher.py
```
✅ DSL Parser (8 queries parsed)
✅ Alert Matching (1 match found)
🎉 All alert matcher tests PASSED!
```

### Real Scraper
```
# In Flower, you should see:
scrape_listing → SUCCESS
parse_listing → SUCCESS
normalize_listing → SUCCESS
deduplicate_listing → SUCCESS
estimate_price → SUCCESS (or FAILURE if no comparables)
classify_risk → SUCCESS
calculate_score → SUCCESS
post_to_channel → SUCCESS (if approved)
match_alerts → SUCCESS (if approved)
```

## ❗ Common Issues

### Import Errors
```bash
# Fix: Install dependencies
pip install -e ".[dev]"
```

### Database Connection Failed
```bash
# Fix: Start database
docker-compose up -d db
sleep 5
```

### Tasks Not Processing
```bash
# Fix: Restart workers
docker-compose restart worker beat
```

### No Comparables Found
```
# Expected: Need more data
# Fix: Scrape more pages
docker-compose exec worker scrapy crawl mobile_bg -a pages=10
```

## 📚 More Info

See [TESTING.md](TESTING.md) for comprehensive guide.
