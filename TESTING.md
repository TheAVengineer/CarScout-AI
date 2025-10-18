# Testing Guide

This guide covers how to test the CarScout AI pipeline and verify all components are working correctly.

## Prerequisites

1. **Install Dependencies**
   ```bash
   # Run the setup script
   ./scripts/dev_setup.sh
   
   # Or manually:
   pip install -e ".[dev]"
   ```

2. **Start Services**
   ```bash
   # Start PostgreSQL, Redis, and Celery workers
   docker-compose up -d
   
   # Wait for services to be ready (~10 seconds)
   sleep 10
   ```

3. **Initialize Database**
   ```bash
   # Create tables and seed initial data
   python scripts/seed_database.py
   ```

## Testing Methods

### Method 1: Quick End-to-End Test (Recommended)

Test the complete pipeline with a synthetic listing:

```bash
python scripts/test_pipeline.py
```

**What it tests:**
- ✅ Parse: HTML → structured data extraction
- ✅ Normalize: Brand/model normalization
- ✅ Dedupe: Duplicate detection (4 methods)
- ✅ Price: Comparable-based price estimation
- ✅ AI Risk: Rule-based risk classification
- ✅ Score: Final scoring and approval logic

**Expected output:**
```
🧪 CarScout AI - End-to-End Pipeline Test
============================================================

📝 Creating test listing...
✅ Created test listing: 550e8400-e29b-41d4-a716-446655440000

🔄 Testing pipeline stages...

1️⃣  Testing PARSE task...
   ✅ Parse complete: parsed
   📋 Normalized listing: 660e9511-f39c-52e5-b827-557766551111

2️⃣  Testing NORMALIZE task...
   ✅ Normalize complete: normalized

3️⃣  Testing DEDUPE task...
   ✅ Dedupe complete: not_duplicate

4️⃣  Testing PRICE task...
   ⚠️  Price task failed (expected if no comparable listings)

5️⃣  Testing AI RISK task...
   ✅ AI Risk complete: green

6️⃣  Testing SCORE task...
   ✅ Score complete: 6.5

📊 Checking final state...
   Brand: BMW
   Model: X5
   Price: 35000 BGN
   Year: 2018
   Mileage: 120000 km
   Fuel: diesel
   Gearbox: automatic
   Is Duplicate: False
   
   Score: 6.50/10
   State: draft
   Price Score: 3.00
   Risk Penalty: 0.00
   Freshness: 0.50

✅ Pipeline test PASSED!
```

### Method 2: Test Alert Matching

Test the DSL parser and alert matching system:

```bash
python scripts/test_alert_matcher.py
```

**What it tests:**
- ✅ DSL Query Parsing (8 sample queries)
- ✅ Alert Matching Logic
- ✅ Plan-based Rate Limiting
- ✅ Multi-language Support (BG/EN)

**Expected output:**
```
🧪 CarScout AI - Alert Matcher Tests

🧪 Testing Alert DSL Parser
============================================================

📝 Query: 'BMW X5 diesel <25000 2016+ <180000km automatic Sofia'
   Parsed:
     brand: BMW
     model: X5
     fuel: diesel
     max_price: 25000
     min_year: 2016
     max_mileage: 180000
     gearbox: automatic
     region: София-град

... (more queries)

✅ DSL Parser test complete!

🧪 Testing Alert Matching
============================================================

📝 Creating test user...
   ✅ User created: 12345678

📝 Creating test alerts...
   ✅ Created 3 alerts

📝 Creating test listing...
   ✅ Listing created: BMW X5

🔍 Testing alert matching...

📊 Found 1 matching alerts:
   ✅ Alert: 'BMW X5 diesel <35000 2015+ automatic'
      User: test_user
      Active: True

✅ All alert matcher tests PASSED!
```

### Method 3: Real Scraper Test

Test with actual data from Mobile.bg:

```bash
# Scrape 1 page from Mobile.bg
docker-compose exec worker scrapy crawl mobile_bg -a pages=1

# Monitor progress in Flower
open http://localhost:5555
```

**What it tests:**
- ✅ Real website scraping
- ✅ Complete pipeline with live data
- ✅ All 9 stages in sequence
- ✅ Celery task chaining
- ✅ Error handling

**Monitor in Flower:**
1. Open http://localhost:5555
2. Go to "Tasks" tab
3. Watch tasks execute: `scrape` → `parse_listing` → `normalize_listing` → `deduplicate_listing` → `estimate_price` → `classify_risk` → `calculate_score` → `post_to_channel` → `match_alerts`

### Method 4: Manual Task Testing

Test individual tasks directly:

```python
from workers.pipeline.tasks.parse import parse_listing
from workers.pipeline.tasks.normalize import normalize_listing
from workers.pipeline.tasks.score import calculate_score

# Test parse
result = parse_listing.delay("listing-id-here")
print(result.get(timeout=10))

# Test normalize
result = normalize_listing.delay("normalized-id-here")
print(result.get(timeout=10))

# Test score
result = calculate_score.delay("normalized-id-here")
print(result.get(timeout=10))
```

## Monitoring

### Flower (Celery UI)
- **URL**: http://localhost:5555
- **Features**: Task monitoring, worker stats, task history

### PostgreSQL
```bash
# Connect to database
docker-compose exec db psql -U carscout_user -d carscout_db

# Check listings
SELECT COUNT(*) FROM listing_normalized;

# Check scores
SELECT ln.normalized_brand, ln.normalized_model, s.total_score, s.state
FROM score s
JOIN listing_normalized ln ON s.listing_id = ln.id
ORDER BY s.created_at DESC
LIMIT 10;

# Check duplicates
SELECT COUNT(*) FROM listing_normalized WHERE is_duplicate = true;

# Check alerts
SELECT u.telegram_username, a.query, a.is_active, a.match_count
FROM alert a
JOIN "user" u ON a.user_id = u.id
ORDER BY a.created_at DESC;
```

### Logs
```bash
# Worker logs
docker-compose logs -f worker

# Beat (scheduler) logs
docker-compose logs -f beat

# API logs (when implemented)
docker-compose logs -f api
```

## Common Issues

### 1. Import Errors (bs4, numpy, etc.)
**Problem**: `ModuleNotFoundError: No module named 'bs4'`

**Solution**:
```bash
pip install -e ".[dev]"
# or
./scripts/dev_setup.sh
```

### 2. Database Connection Error
**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
```bash
# Check if containers are running
docker-compose ps

# Restart services
docker-compose restart db

# Reinitialize database
python scripts/seed_database.py
```

### 3. Celery Worker Not Processing Tasks
**Problem**: Tasks stuck in "PENDING" state

**Solution**:
```bash
# Restart workers
docker-compose restart worker beat

# Check worker logs
docker-compose logs worker

# Verify Redis connection
docker-compose exec worker redis-cli -h redis ping
```

### 4. No Comparables Found (Price Estimation)
**Problem**: `estimate_price` task returns "no comparables found"

**Expected**: This is normal for new databases. The pricing model needs at least 30 similar listings to estimate prices accurately.

**Solution**:
```bash
# Scrape more data
docker-compose exec worker scrapy crawl mobile_bg -a pages=10

# Or wait for more listings to accumulate
```

### 5. OpenAI API Key Missing
**Problem**: `classify_risk` task fails with "API key not configured"

**Solution**:
```bash
# Add to .env file
echo "OPENAI_API_KEY=your-key-here" >> .env

# Restart services
docker-compose restart worker
```

## Testing Checklist

Before deploying to production, verify:

- [ ] **Pipeline Stages**
  - [ ] Parse extracts data correctly
  - [ ] Normalize maps brands/models
  - [ ] Dedupe detects duplicates
  - [ ] Price estimates are reasonable
  - [ ] AI classifies risk correctly
  - [ ] Score calculation works
  - [ ] Notifications trigger

- [ ] **Alert System**
  - [ ] DSL parser handles all query types
  - [ ] Alert matching is accurate
  - [ ] Rate limiting enforced (Free: 30min delay)
  - [ ] Daily caps respected (Free: 10/day)
  - [ ] Notifications sent to Telegram

- [ ] **Data Quality**
  - [ ] No duplicate listings in database
  - [ ] Prices are in correct currency
  - [ ] Years are valid (1990-2025)
  - [ ] Mileage is reasonable
  - [ ] All required fields populated

- [ ] **Performance**
  - [ ] Tasks complete within timeout (60s)
  - [ ] No memory leaks (monitor with `docker stats`)
  - [ ] Database queries are efficient (use EXPLAIN)
  - [ ] API responses < 500ms (when implemented)

- [ ] **Error Handling**
  - [ ] Tasks retry on failure
  - [ ] Invalid HTML handled gracefully
  - [ ] Missing fields don't crash pipeline
  - [ ] Network errors are logged

## Next Steps

After testing:

1. **Fix any failing tests** - Address issues before proceeding
2. **Load test** - Run with 1000+ listings to check performance
3. **Set up monitoring** - Configure Grafana dashboards
4. **Deploy to staging** - Test in production-like environment
5. **Beta launch** - Invite select users for feedback

## Getting Help

If tests fail or you encounter issues:

1. Check the error message in test output
2. Review logs: `docker-compose logs -f worker`
3. Check Flower: http://localhost:5555
4. Query database to inspect data
5. Create an issue on GitHub with:
   - Error message
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant logs

---

**Happy Testing! 🧪**
