"""
Seed database with large dataset from Mobile.bg
Scrapes listings and processes them through the pipeline
"""
import sys
import time
from subprocess import run, PIPE
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw, ListingNormalized
from sqlalchemy import func


def check_current_data():
    """Check current database state"""
    with get_sync_session() as session:
        raw_count = session.query(func.count(ListingRaw.id)).scalar()
        normalized_count = session.query(func.count(ListingNormalized.id)).scalar()
        non_dup_count = session.query(func.count(ListingNormalized.id)).filter(
            ListingNormalized.is_duplicate == False
        ).scalar()
        
        print("📊 Current Database State:")
        print(f"   Raw listings: {raw_count}")
        print(f"   Normalized listings: {normalized_count}")
        print(f"   Non-duplicate listings: {non_dup_count}")
        print()
        
        # Show brand distribution
        brands = session.query(
            ListingNormalized.brand_id,
            func.count(ListingNormalized.id)
        ).filter(
            ListingNormalized.is_duplicate == False
        ).group_by(
            ListingNormalized.brand_id
        ).having(
            func.count(ListingNormalized.id) >= 2
        ).all()
        
        if brands:
            print("📈 Brand Distribution (2+ listings):")
            for brand, count in brands:
                print(f"   {brand or 'Unknown'}: {count} listings")
        
        return raw_count, normalized_count


def run_spider(max_listings=100):
    """Run Scrapy spider to scrape Mobile.bg listings"""
    print(f"\n🕷️  Starting Mobile.bg spider (target: {max_listings} listings)...")
    print("   This may take several minutes due to rate limiting...\n")
    
    # Run spider with custom settings
    cmd = [
        sys.executable,
        "-m", "scrapy",
        "crawl", "mobile_bg",
        "-s", f"CLOSESPIDER_ITEMCOUNT={max_listings}",  # Stop after N items
        "-s", "CONCURRENT_REQUESTS=2",  # Slightly faster
        "-s", "DOWNLOAD_DELAY=2",  # 2 second delay
        "-L", "INFO",  # Log level
    ]
    
    # Change to scrape directory
    scrape_dir = Path(__file__).parent.parent / "workers" / "scrape"
    
    result = run(cmd, cwd=str(scrape_dir), capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ Spider failed!")
        print(result.stderr)
        return False
    
    print("✅ Spider completed!")
    return True


def trigger_pipeline_for_all():
    """Trigger pipeline processing for all raw listings without normalized data"""
    print("\n⚙️  Triggering pipeline for unprocessed listings...")
    
    from workers.pipeline.tasks import parse
    
    with get_sync_session() as session:
        # Find raw listings without normalized data
        unprocessed = session.query(ListingRaw).filter(
            ~ListingRaw.normalized.has()
        ).limit(100).all()
        
        if not unprocessed:
            print("   No unprocessed listings found!")
            return
        
        print(f"   Found {len(unprocessed)} unprocessed listings")
        print(f"   Queueing Celery tasks...\n")
        
        for i, raw in enumerate(unprocessed, 1):
            try:
                # Queue parse task (will trigger full pipeline)
                result = parse.parse_listing.delay(str(raw.id))
                print(f"   [{i}/{len(unprocessed)}] Queued: {raw.id}")
                time.sleep(0.1)  # Small delay to avoid overwhelming queue
            except Exception as e:
                print(f"   ❌ Failed to queue {raw.id}: {e}")
        
        print(f"\n✅ Queued {len(unprocessed)} listings for processing")
        print("   Monitor Celery worker to see progress...")


def show_progress():
    """Show processing progress"""
    print("\n📊 Processing Progress:")
    
    with get_sync_session() as session:
        total_raw = session.query(func.count(ListingRaw.id)).scalar()
        processed = session.query(func.count(ListingNormalized.id)).scalar()
        non_dup = session.query(func.count(ListingNormalized.id)).filter(
            ListingNormalized.is_duplicate == False
        ).scalar()
        
        print(f"   Total scraped: {total_raw}")
        print(f"   Processed: {processed} ({processed/total_raw*100:.1f}%)")
        print(f"   Non-duplicates: {non_dup}")
        
        # Show brands with 5+ listings (ready for price estimation)
        print("\n🎯 Brands Ready for Price Estimation (5+ listings):")
        ready_brands = session.query(
            ListingNormalized.brand_id,
            ListingNormalized.model_id,
            func.count(ListingNormalized.id)
        ).filter(
            ListingNormalized.is_duplicate == False
        ).group_by(
            ListingNormalized.brand_id,
            ListingNormalized.model_id
        ).having(
            func.count(ListingNormalized.id) >= 5
        ).all()
        
        if ready_brands:
            for brand, model, count in ready_brands:
                print(f"   ✅ {brand} {model}: {count} listings")
        else:
            print("   ⏳ Not yet - need more data...")


def main():
    """Main execution"""
    print("=" * 70)
    print("🚀 CarScout AI - Large Dataset Seeding")
    print("=" * 70)
    
    # Check current state
    check_current_data()
    
    # Ask user for target size
    print("\n" + "=" * 70)
    target = input("How many NEW listings to scrape? (default: 100, max: 1000): ").strip()
    
    if not target:
        target = 100
    else:
        try:
            target = int(target)
            if target > 1000:
                print("⚠️  Limiting to 1000 listings to avoid rate limiting")
                target = 1000
        except ValueError:
            print("Invalid input, using default: 100")
            target = 100
    
    print(f"\n🎯 Target: {target} new listings")
    print("⚠️  Note: This will take approximately {:.1f} minutes".format(target * 2 / 60))
    print("   (2 seconds delay per listing due to rate limiting)\n")
    
    proceed = input("Proceed? (y/N): ").strip().lower()
    if proceed != 'y':
        print("❌ Cancelled")
        return
    
    print("\n" + "=" * 70)
    
    # Step 1: Run spider
    if not run_spider(target):
        print("\n❌ Failed to scrape listings")
        return
    
    # Step 2: Check what we got
    print("\n" + "=" * 70)
    raw_count, _ = check_current_data()
    
    # Step 3: Trigger pipeline
    print("\n" + "=" * 70)
    trigger_pipeline_for_all()
    
    # Step 4: Show final progress
    print("\n" + "=" * 70)
    print("\n⏳ Processing in background...")
    print("   Wait a few minutes for Celery to process all listings")
    print("\n💡 To check progress, run:")
    print("   python scripts/seed_large_dataset.py --status")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        show_progress()
    else:
        main()
