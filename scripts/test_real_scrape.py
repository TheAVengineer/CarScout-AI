"""
Test script to scrape a real Mobile.bg listing and process through pipeline
"""
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw
from workers.pipeline.tasks.parse import parse_listing


def test_with_existing_listing():
    """Test pipeline with an existing raw listing"""
    print("🔍 Checking for existing raw listings...")
    
    with get_sync_session() as session:
        # Get most recent raw listing
        raw = session.query(ListingRaw).order_by(ListingRaw.created_at.desc()).first()
        
        if not raw:
            print("❌ No raw listings found in database")
            print("   Run the scraper first to populate some data")
            return
        
        print(f"✅ Found listing: {raw.id}")
        print(f"   Source: {raw.source_id}")
        print(f"   Site ID: {raw.site_ad_id}")
        print(f"   Created: {raw.created_at}")
        
        # Trigger parse task
        print("\n📤 Queueing parse task...")
        result = parse_listing.apply_async(args=[str(raw.id)])
        print(f"   Task ID: {result.id}")
        
        # Wait for completion
        print("\n⏳ Waiting for pipeline to complete...")
        print("   (This will process: parse → normalize → dedupe → price → risk → llm → score)")
        
        timeout = 120
        start = time.time()
        
        while not result.ready() and (time.time() - start) < timeout:
            time.sleep(2)
            elapsed = int(time.time() - start)
            print(f"   ... {elapsed}s elapsed", end='\r')
        
        if result.ready():
            if result.successful():
                print(f"\n✅ Pipeline completed successfully!")
                print(f"   Result: {result.result}")
            else:
                print(f"\n❌ Pipeline failed:")
                print(f"   Error: {result.result}")
        else:
            print(f"\n⏱️  Pipeline timeout after {timeout}s")
            print("   Check worker logs for details")


if __name__ == '__main__':
    test_with_existing_listing()
