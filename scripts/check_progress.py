"""Check scraping and processing progress"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw, ListingNormalized, Score
from sqlalchemy import func
import redis


def main():
    print("=" * 70)
    print("📊 CARSCOUT AI - DATABASE PROGRESS")
    print("=" * 70)
    
    with get_sync_session() as session:
        # Overall stats
        total_raw = session.query(func.count(ListingRaw.id)).scalar() or 0
        total_normalized = session.query(func.count(ListingNormalized.id)).scalar() or 0
        total_non_dup = session.query(func.count(ListingNormalized.id)).filter(
            ListingNormalized.is_duplicate == False
        ).scalar() or 0
        total_scored = session.query(func.count(Score.id)).scalar() or 0
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Raw listings scraped:    {total_raw:,}")
        print(f"   Normalized (processed):  {total_normalized:,} ({total_normalized/max(total_raw,1)*100:.1f}%)")
        print(f"   Non-duplicates:          {total_non_dup:,} ({total_non_dup/max(total_normalized,1)*100:.1f}%)")
        print(f"   Scored:                  {total_scored:,}")
        
        # Processing pipeline status
        unprocessed = total_raw - total_normalized
        if unprocessed > 0:
            print(f"\n⏳ Unprocessed: {unprocessed:,} listings waiting")
        else:
            print(f"\n✅ All scraped listings have been processed!")
        
        # Brand distribution
        print(f"\n🏷️  Brand Distribution (Non-Duplicates):")
        brands = session.query(
            ListingNormalized.brand_id,
            func.count(ListingNormalized.id)
        ).filter(
            ListingNormalized.is_duplicate == False
        ).group_by(
            ListingNormalized.brand_id
        ).order_by(
            func.count(ListingNormalized.id).desc()
        ).limit(15).all()
        
        if brands:
            for brand, count in brands:
                brand_name = brand or "Unknown"
                bar = "█" * min(50, count)
                print(f"   {brand_name:15s} {count:4d} {bar}")
        else:
            print("   No data yet - start scraping!")
        
        # Ready for price estimation (5+ listings)
        print(f"\n🎯 Ready for Price Estimation (5+ listings per model):")
        ready = session.query(
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
        ).order_by(
            func.count(ListingNormalized.id).desc()
        ).all()
        
        if ready:
            for brand, model, count in ready:
                brand_name = brand or "Unknown"
                model_name = model or "Unknown"
                print(f"   ✅ {brand_name:10s} {model_name:15s} {count:3d} listings")
        else:
            print("   ⏳ None yet - need more variety!")
            print("   💡 Tip: Scrape 500+ listings to get enough comparables")
        
        # Score distribution
        print(f"\n📊 Score Distribution:")
        score_ranges = [
            ("Excellent (8-10)", 8, 10),
            ("Good (6-8)", 6, 8),
            ("Fair (4-6)", 4, 6),
            ("Poor (2-4)", 2, 4),
            ("Rejected (0-2)", 0, 2),
        ]
        
        for label, min_score, max_score in score_ranges:
            count = session.query(func.count(Score.id)).filter(
                Score.score >= min_score,
                Score.score < max_score
            ).scalar() or 0
            
            if count > 0:
                bar = "█" * min(30, count)
                print(f"   {label:20s} {count:4d} {bar}")
        
    # Check Celery queue
    try:
        r = redis.Redis(host='localhost', port=6379, db=1, decode_responses=False)
        queue_len = r.llen('celery')
        print(f"\n⚙️  Celery Queue:")
        print(f"   Pending tasks: {queue_len}")
        if queue_len > 0:
            print(f"   ⏳ Processing in progress...")
        else:
            print(f"   ✅ Queue empty - all caught up!")
    except:
        print(f"\n⚠️  Could not connect to Redis (Celery queue)")
    
    print("\n" + "=" * 70)
    print("💡 Next Steps:")
    
    if total_raw == 0:
        print("   1. Start scraping: scrapy crawl mobile_bg_sitemap -s CLOSESPIDER_ITEMCOUNT=100")
        print("   2. Start Celery worker to process listings")
    elif unprocessed > 0:
        print(f"   1. Wait for Celery to process {unprocessed} listings")
        print("   2. Or restart Celery worker if stuck")
    elif not ready:
        print("   1. Scrape more listings (need 5+ per brand/model)")
        print("   2. Target: 500+ listings for good coverage")
    else:
        print("   1. Test pipeline: python scripts/trigger_pipeline.py")
        print("   2. Check specific scores in database")
        print("   3. Setup Telegram notifications")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
