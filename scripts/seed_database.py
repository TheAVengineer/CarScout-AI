#!/Users/alexandervidenov/Desktop/CarScout-AI/.venv/bin/python3
"""
Seed the database with initial listings for price comparison baseline

This script:
1. Scrapes all 10 brands in parallel (300 listings)
2. Waits for scraping to complete
3. Processes all listings (parse, normalize, score)
4. Creates baseline data for future comparisons

Run this ONCE before starting the automated system.
"""
import sys
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from workers.pipeline.tasks.scrape_tasks import scrape_all_brands
from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw, ListingNormalized, Score

def check_database_status():
    """Check current database counts"""
    session = get_sync_session()
    try:
        raw_count = session.query(ListingRaw).count()
        normalized_count = session.query(ListingNormalized).count()
        scored_count = session.query(Score).count()
        return raw_count, normalized_count, scored_count
    finally:
        session.close()

def main():
    print("=" * 60)
    print("🌱 CarScout AI - Database Seeding")
    print("=" * 60)
    print()
    
    # Check initial status
    print("📊 Current database status:")
    raw, normalized, scored = check_database_status()
    print(f"  Raw listings: {raw}")
    print(f"  Normalized: {normalized}")
    print(f"  Scored: {scored}")
    print()
    
    if raw >= 100:
        print("⚠️  Database already has 100+ listings.")
        print("   Do you want to add more? (y/n): ", end="")
        if input().strip().lower() != 'y':
            print("❌ Seeding cancelled")
            return
        print()
    
    # Start seeding
    print("🚀 Starting database seeding...")
    print("   This will scrape ~300 listings (30 per brand)")
    print("   Estimated time: 5-7 minutes")
    print()
    
    # Trigger scraping task
    print("📋 Scheduling scraping task...")
    
    try:
        task = scrape_all_brands.delay()
        print(f"   ✅ Task ID: {task.id}")
        print(f"   Status: {task.status}")
        print()
    except Exception as e:
        print(f"   ❌ Failed to schedule task: {e}")
        print()
        print("   This usually means Celery workers aren't running.")
        print("   Make sure workers are started:")
        print("     ./scripts/start_all.sh")
        print()
        print("   Or run scraping directly without Celery:")
        print("     .venv/bin/python3 scripts/trigger_scrape.py")
        return
    
    # Monitor progress
    print("⏳ Waiting for scraping to complete...")
    print("   (Monitor logs: tail -f logs/celery-worker.log)")
    print()
    
    dots = 0
    while task.status not in ['SUCCESS', 'FAILURE']:
        print(f"\r   Status: {task.status} {'.' * (dots % 4)}", end="")
        dots += 1
        time.sleep(2)
    
    print()
    print()
    
    if task.status == 'FAILURE':
        print(f"❌ Scraping failed: {task.result}")
        print("   Check logs for details: tail -50 logs/celery-worker.log")
        return
    
    print("✅ Scraping completed!")
    print()
    
    # Check final status
    print("📊 Final database status:")
    raw, normalized, scored = check_database_status()
    print(f"  Raw listings: {raw}")
    print(f"  Normalized: {normalized}")
    print(f"  Scored: {scored}")
    print()
    
    print("=" * 60)
    print("🎉 Database seeding complete!")
    print()
    print("Next steps:")
    print("1. Complete the parse task (workers/pipeline/tasks/parse.py)")
    print("2. Test pipeline: tail -f logs/celery-worker.log")
    print("3. Start automated system: ./scripts/start_all.sh")
    print()
    print("The system will now compare new listings against this baseline")
    print("to identify great deals!")
    print("=" * 60)

if __name__ == "__main__":
    main()

from libs.domain.database import get_sync_session
from libs.domain.models import Source, Plan, BrandModel
from libs.domain.normalization import seed_brand_models


def seed_sources():
    """Seed marketplace sources"""
    session = get_sync_session()
    
    sources_data = [
        {
            "name": "mobile_bg",
            "base_url": "https://www.mobile.bg",
            "enabled": True,
            "crawl_interval_s": 120,
        },
        {
            "name": "cars_bg",
            "base_url": "https://www.cars.bg",
            "enabled": True,
            "crawl_interval_s": 180,
        },
        {
            "name": "olx_bg",
            "base_url": "https://www.olx.bg",
            "enabled": False,  # Not implemented yet
            "crawl_interval_s": 300,
        },
    ]
    
    for source_data in sources_data:
        existing = session.query(Source).filter_by(name=source_data["name"]).first()
        if not existing:
            source = Source(**source_data)
            session.add(source)
            print(f"✅ Added source: {source_data['name']}")
        else:
            print(f"⏭️  Source already exists: {source_data['name']}")
    
    session.commit()
    session.close()


def seed_plans_data():
    """Seed subscription plans"""
    session = get_sync_session()
    
    plans_data = [
        {
            "name": "Free",
            "limits": {"max_alerts": 3, "delay_minutes": 30, "daily_alert_cap": 10},
            "price_bgn": 0,
        },
        {
            "name": "Premium",
            "limits": {"max_alerts": 10, "delay_minutes": 0, "daily_alert_cap": 50},
            "price_bgn": 19.99,
        },
        {
            "name": "Pro",
            "limits": {"max_alerts": 999, "delay_minutes": 0, "daily_alert_cap": 999},
            "price_bgn": 39.99,
        },
    ]
    
    for plan_data in plans_data:
        existing = session.query(Plan).filter_by(name=plan_data["name"]).first()
        if not existing:
            plan = Plan(**plan_data)
            session.add(plan)
            print(f"✅ Added plan: {plan_data['name']}")
        else:
            print(f"⏭️  Plan already exists: {plan_data['name']}")
    
    session.commit()
    session.close()


def main():
    """Run all seed functions"""
    print("🌱 Seeding database...")
    print()
    
    print("📦 Seeding sources...")
    seed_sources()
    print()
    
    print("💳 Seeding plans...")
    seed_plans_data()
    print()
    
    print("🚗 Seeding brand/model mappings...")
    seed_brand_models()
    print()
    
    print("✅ Database seeding complete!")


if __name__ == "__main__":
    main()
