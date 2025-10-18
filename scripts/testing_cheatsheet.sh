#!/usr/bin/env bash
# CarScout AI - Testing Cheatsheet
# Quick copy-paste commands for testing

cat << 'EOF'

╔════════════════════════════════════════════════════════════════╗
║              🧪 CarScout AI - Testing Cheatsheet              ║
╚════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────┐
│ 🚀 QUICK START                                                 │
└─────────────────────────────────────────────────────────────────┘

# Start all services
docker-compose up -d

# Run all tests
./scripts/run_tests.sh


┌─────────────────────────────────────────────────────────────────┐
│ 📝 INDIVIDUAL TESTS                                            │
└─────────────────────────────────────────────────────────────────┘

# Test 1: Setup verification
python scripts/test_setup.py

# Test 2: Pipeline end-to-end
python scripts/test_pipeline.py

# Test 3: Alert matcher
python scripts/test_alert_matcher.py

# Test 4: Real scraper (1 page)
docker-compose exec worker scrapy crawl mobile_bg -a pages=1


┌─────────────────────────────────────────────────────────────────┐
│ 🔍 MONITORING                                                  │
└─────────────────────────────────────────────────────────────────┘

# Flower (task monitor)
open http://localhost:5555

# View all logs
docker-compose logs -f

# View worker logs only
docker-compose logs -f worker

# View API logs only
docker-compose logs -f api


┌─────────────────────────────────────────────────────────────────┐
│ 💾 DATABASE QUERIES                                            │
└─────────────────────────────────────────────────────────────────┘

# Connect to database
docker-compose exec db psql -U carscout_user -d carscout_db

# Then run SQL:
SELECT COUNT(*) FROM listing_normalized;

SELECT ln.normalized_brand, ln.normalized_model, s.total_score, s.state
FROM score s
JOIN listing_normalized ln ON s.listing_id = ln.id
ORDER BY s.created_at DESC
LIMIT 10;

SELECT COUNT(*) FROM listing_normalized WHERE is_duplicate = true;


┌─────────────────────────────────────────────────────────────────┐
│ 🔧 SERVICE MANAGEMENT                                          │
└─────────────────────────────────────────────────────────────────┘

# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View service status
docker-compose ps

# Rebuild and restart
docker-compose up -d --build


┌─────────────────────────────────────────────────────────────────┐
│ 🗄️ DATABASE MANAGEMENT                                        │
└─────────────────────────────────────────────────────────────────┘

# Run migrations
alembic upgrade head

# Seed data
python scripts/seed_database.py

# Reset database (⚠️ DELETES ALL DATA)
docker-compose down -v
docker-compose up -d db
sleep 5
alembic upgrade head
python scripts/seed_database.py


┌─────────────────────────────────────────────────────────────────┐
│ 🕷️ SCRAPING COMMANDS                                          │
└─────────────────────────────────────────────────────────────────┘

# Mobile.bg (1 page - quick test)
docker-compose exec worker scrapy crawl mobile_bg -a pages=1

# Mobile.bg (10 pages - more data)
docker-compose exec worker scrapy crawl mobile_bg -a pages=10

# Cars.bg
docker-compose exec worker scrapy crawl cars_bg -a pages=5

# OLX
docker-compose exec worker scrapy crawl olx -a pages=5


┌─────────────────────────────────────────────────────────────────┐
│ 🐛 DEBUGGING                                                   │
└─────────────────────────────────────────────────────────────────┘

# Check Celery workers
docker-compose exec worker celery -A workers.pipeline.celery_app inspect active

# Check Celery stats
docker-compose exec worker celery -A workers.pipeline.celery_app inspect stats

# Check Redis queue
docker-compose exec redis redis-cli
> LLEN celery
> KEYS *

# Check worker health
curl http://localhost:5555/api/workers


┌─────────────────────────────────────────────────────────────────┐
│ ⚡ COMMON FIXES                                                │
└─────────────────────────────────────────────────────────────────┘

# Fix: Import errors (bs4, numpy, etc.)
pip install -e ".[dev]"

# Fix: Database connection failed
docker-compose up -d db
sleep 5

# Fix: Tasks not processing
docker-compose restart worker beat

# Fix: Need more test data
docker-compose exec worker scrapy crawl mobile_bg -a pages=10


┌─────────────────────────────────────────────────────────────────┐
│ 📊 EXPECTED TEST RESULTS                                       │
└─────────────────────────────────────────────────────────────────┘

test_setup.py:
  ✅ Database Connection
  ✅ Sources (3 found)
  ✅ Plans (Free, Premium, Pro)
  ✅ Brand/Model Mappings (17+ mappings)
  🎉 All tests passed!

test_pipeline.py:
  ✅ Parse complete
  ✅ Normalize complete
  ✅ Dedupe complete
  ⚠️  Price complete (may fail if no comparables)
  ✅ AI Risk complete
  ✅ Score complete
  🎉 Pipeline test PASSED!

test_alert_matcher.py:
  ✅ DSL Parser (8 queries parsed)
  ✅ Alert Matching (1 match found)
  🎉 All alert matcher tests PASSED!


┌─────────────────────────────────────────────────────────────────┐
│ 📚 DOCUMENTATION                                               │
└─────────────────────────────────────────────────────────────────┘

TESTING.md              - Comprehensive testing guide
TESTING-QUICK-REF.md    - Quick reference for commands
TESTING-FLOW.md         - Visual diagrams and flows
TESTING-README.md       - Documentation overview


┌─────────────────────────────────────────────────────────────────┐
│ 🎯 RECOMMENDED WORKFLOW                                        │
└─────────────────────────────────────────────────────────────────┘

# First time:
1. docker-compose up -d
2. python scripts/test_setup.py
3. ./scripts/run_tests.sh

# Daily development:
1. python scripts/test_setup.py
2. [make your changes]
3. python scripts/test_pipeline.py
4. python scripts/test_alert_matcher.py

# Before deployment:
1. ./scripts/run_tests.sh
2. docker-compose exec worker scrapy crawl mobile_bg -a pages=10
3. open http://localhost:5555


╔════════════════════════════════════════════════════════════════╗
║  💡 TIP: Save this file or run: ./scripts/testing_cheatsheet  ║
╚════════════════════════════════════════════════════════════════╝

EOF
