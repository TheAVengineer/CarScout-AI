"""
🚀 QUICK START: Seed Database with Large Dataset
==================================================

This guide shows you THREE ways to populate your database with hundreds or thousands of listings.

OPTION 1: Use Sitemap Spider (RECOMMENDED - Fastest & Most Reliable)
---------------------------------------------------------------------
The sitemap spider discovers URLs from Mobile.bg's sitemap and scrapes them efficiently.

Step 1: Start Celery worker (in separate terminal):
    cd C:\CarScout-AI
    .\venv\Scripts\activate
    celery -A workers.pipeline.celery_app worker --loglevel=info --pool=solo

Step 2: Run sitemap spider:
    cd C:\CarScout-AI\workers\scrape
    scrapy crawl mobile_bg_sitemap -s CLOSESPIDER_ITEMCOUNT=500

    Options:
    - CLOSESPIDER_ITEMCOUNT=N    : Stop after scraping N items (default: unlimited)
    - CONCURRENT_REQUESTS=N       : Parallel requests (default: 3, max: 5)
    - DOWNLOAD_DELAY=N           : Seconds between requests (default: 0.5)

Step 3: Monitor progress:
    python scripts/check_progress.py

Expected time: ~500 listings in 5-10 minutes


OPTION 2: Use Direct Search Spider (Good for Specific Filters)
---------------------------------------------------------------
This spider searches Mobile.bg with specific criteria (brand, price range, etc.)

Step 1: Start Celery worker (same as above)

Step 2: Edit the spider to set your filters:
    File: workers/scrape/carscout/spiders/mobile_bg.py
    
    Modify start_requests() to add search parameters:
        base_url = "https://m.mobile.bg/obiavi/avtomobili-dzhipove"
        params = {
            'slink': 'e6t7p',  # Category
            'price_from': '5000',
            'price_to': '50000',
            # Add more filters as needed
        }

Step 3: Remove the 3-listing limit:
    Line 82-83: Comment out or remove:
        # if listing_count >= 3:
        #     break

Step 4: Run spider:
    cd C:\CarScout-AI\workers\scrape
    scrapy crawl mobile_bg -s CLOSESPIDER_ITEMCOUNT=500


OPTION 3: Use Automated Seeding Script (EASIEST)
-------------------------------------------------
This script does everything automatically: scrapes, processes, and shows progress.

Step 1: Start Celery worker (same as above)

Step 2: Run seeding script:
    python scripts/seed_large_dataset.py

    It will:
    - Show current database state
    - Ask how many listings to scrape (1-1000)
    - Run spider automatically
    - Queue all listings for processing
    - Show progress

Step 3: Check progress:
    python scripts/seed_large_dataset.py --status


CURRENT DATABASE STATUS
-----------------------
Run this to see what you have now:

    python -c "from libs.domain.database import get_sync_session; \
    from libs.domain.models import ListingRaw, ListingNormalized; \
    from sqlalchemy import func; \
    s = get_sync_session(); \
    print(f'Raw: {s.query(func.count(ListingRaw.id)).scalar()}'); \
    print(f'Normalized: {s.query(func.count(ListingNormalized.id)).scalar()}'); \
    print(f'Non-duplicates: {s.query(func.count(ListingNormalized.id)).filter(ListingNormalized.is_duplicate==False).scalar()}')"


MONITORING PIPELINE PROCESSING
-------------------------------
Once listings are scraped, they need to be processed through the pipeline.

Check Celery queue length:
    python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=1); \
    print(f'Queue length: {r.llen(\"celery\")}')"

Watch Celery worker logs:
    (It shows real-time processing in the terminal where Celery is running)

Check processed listings:
    python scripts/check_progress.py


TROUBLESHOOTING
---------------

Problem: Spider not finding any listings
Solution: Mobile.bg may have changed their HTML. Check logs and update selectors.

Problem: Celery queue growing but not processing
Solution: Check Celery worker is running. Restart if needed.

Problem: Duplicate listings being rejected
Solution: This is normal! Deduplication works. Only unique listings are kept.

Problem: Scores still low (1.0/10)
Solution: Need 5+ listings of SAME brand/model for price estimation.
          Keep scraping until you have variety!


RECOMMENDED SCRAPING STRATEGY
------------------------------

For best results, scrape in phases:

Phase 1: Initial Dataset (100 listings)
    - Run: scrapy crawl mobile_bg_sitemap -s CLOSESPIDER_ITEMCOUNT=100
    - Goal: Get variety of brands/models
    - Time: ~2-3 minutes

Phase 2: Build Comparables (500 listings)
    - Run: scrapy crawl mobile_bg_sitemap -s CLOSESPIDER_ITEMCOUNT=500
    - Goal: Get 5+ of popular brands (BMW, Audi, VW, etc.)
    - Time: ~10 minutes

Phase 3: Large Dataset (2000+ listings)
    - Run: scrapy crawl mobile_bg_sitemap -s CLOSESPIDER_ITEMCOUNT=2000
    - Goal: Statistical significance for all brands
    - Time: ~30-40 minutes

Phase 4: Full Scrape (10,000+ listings)
    - Run: scrapy crawl mobile_bg_sitemap
    - Goal: Production-ready dataset
    - Time: 2-3 hours
    - Note: Use cron/scheduler for ongoing updates


CHECKING RESULTS
----------------

After scraping and processing, check which brands are ready for pricing:

    python -c "from libs.domain.database import get_sync_session; \
    from libs.domain.models import ListingNormalized; \
    from sqlalchemy import func; \
    s = get_sync_session(); \
    brands = s.query(ListingNormalized.brand_id, ListingNormalized.model_id, \
    func.count(ListingNormalized.id)).filter(ListingNormalized.is_duplicate==False)\
    .group_by(ListingNormalized.brand_id, ListingNormalized.model_id)\
    .having(func.count(ListingNormalized.id) >= 5).all(); \
    print('Brands ready for pricing (5+ listings):'); \
    [print(f'  {b} {m}: {c}') for b,m,c in brands]"


NEXT STEPS AFTER SEEDING
-------------------------

1. Run test pipeline on a listing with comparables:
   python scripts/trigger_pipeline.py

2. Check scores - should be 5.0-9.0 for good deals

3. Set up periodic scraping (every hour/day)

4. Enable Telegram notifications

5. Launch to users! 🚀


QUESTIONS?
----------
- Issue: Data not processing? Check Celery worker is running
- Issue: Rate limited? Increase DOWNLOAD_DELAY to 1-2 seconds
- Issue: Parser errors? Check parser field mappings in parse.py
- Issue: Low scores? Need more comparables of same brand/model
