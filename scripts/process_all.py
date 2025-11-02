"""
Trigger pipeline processing for all unprocessed raw listings
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw, ListingNormalized
from workers.pipeline.tasks import parse


def main():
    print("=" * 70)
    print("⚙️  PROCESSING UNPROCESSED LISTINGS")
    print("=" * 70)
    
    with get_sync_session() as session:
        # Find raw listings without normalized data
        unprocessed = session.query(ListingRaw).outerjoin(
            ListingNormalized,
            ListingRaw.id == ListingNormalized.raw_id
        ).filter(
            ListingNormalized.id == None
        ).limit(1000).all()  # Process max 1000 at a time
        
        if not unprocessed:
            print("\n✅ All listings are already processed!")
            return
        
        print(f"\n📊 Found {len(unprocessed)} unprocessed listings")
        print(f"⏳ This will take approximately {len(unprocessed) * 0.5:.0f} seconds")
        print(f"\n🚀 Queueing tasks to Celery...\n")
        
        success = 0
        failed = 0
        
        for i, raw in enumerate(unprocessed, 1):
            try:
                # Queue parse task (triggers full pipeline: parse → normalize → dedupe → price → risk → score)
                result = parse.parse_listing.delay(str(raw.id))
                
                if i % 10 == 0:
                    print(f"   [{i:4d}/{len(unprocessed)}] Queued ({success} success, {failed} failed)")
                
                success += 1
                time.sleep(0.05)  # Small delay to avoid overwhelming Redis
                
            except Exception as e:
                failed += 1
                if i <= 10:  # Only show first 10 errors
                    print(f"   ❌ Failed to queue {raw.id}: {e}")
        
        print(f"\n✅ Queueing complete!")
        print(f"   Success: {success}")
        print(f"   Failed: {failed}")
        print(f"\n💡 Monitor progress:")
        print(f"   python scripts/check_progress.py")
        print(f"\n💡 Watch Celery worker logs to see processing")
        print("=" * 70)


if __name__ == "__main__":
    main()
