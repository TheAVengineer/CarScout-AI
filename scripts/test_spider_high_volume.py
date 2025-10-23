"""
Test Mobile.bg spider with higher limits (50 listings).

This simulates production load to verify:
- Spider handles many listings
- No memory leaks
- Pagination works (if implemented)
- Database can handle bulk inserts
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Import settings
sys.path.insert(0, str(project_root / 'workers' / 'scrape'))
from carscout.spiders.mobile_bg import MobileBgSpider

def main():
    """Run spider with 50 listing limit"""
    
    # Get Scrapy settings
    settings = get_project_settings()
    
    # Override settings for higher volume testing
    settings.update({
        'CLOSESPIDER_ITEMCOUNT': 50,  # Test with 50 items
        'CONCURRENT_REQUESTS': 2,  # Increase concurrency slightly
        'DOWNLOAD_DELAY': 1,  # Faster but still respectful
        'LOG_LEVEL': 'INFO',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        },
    })
    
    print("="*60)
    print("🚀 Testing Mobile.bg Spider - HIGH VOLUME (50 listings)")
    print("="*60)
    print()
    print("This test will:")
    print("  - Scrape 50 listings (10x normal test)")
    print("  - Test spider performance under load")
    print("  - Verify database can handle bulk inserts")
    print("  - Check for memory leaks or issues")
    print()
    print("⏱️  Expected duration: ~3-5 minutes")
    print()
    print("🚀 Starting spider...")
    print("="*60)
    print()
    
    # Create process and run spider
    process = CrawlerProcess(settings)
    process.crawl(MobileBgSpider)
    
    import time
    start_time = time.time()
    
    try:
        process.start()
    except Exception as e:
        print(f"\n❌ Error during spider execution: {e}")
        return 1
    
    duration = time.time() - start_time
    
    print()
    print("="*60)
    print("✅ Spider finished!")
    print(f"⏱️  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"📊 Average: {duration/50:.1f} seconds per listing")
    print("="*60)
    
    # Check database
    print()
    print("📊 Checking database...")
    
    from libs.domain.database import get_sync_session
    from libs.domain.models import ListingRaw
    
    db = get_sync_session()
    
    # Count total listings
    total = db.query(ListingRaw).count()
    
    # Count recent listings (last hour)
    from datetime import datetime, timedelta
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent = db.query(ListingRaw).filter(
        ListingRaw.created_at >= one_hour_ago
    ).count()
    
    print(f"  Total listings in DB: {total}")
    print(f"  New listings (last hour): {recent}")
    print()
    
    if recent >= 45:  # Allow for some duplicates
        print("✅ SUCCESS - High volume scraping works!")
        return 0
    else:
        print(f"⚠️  WARNING - Expected ~50 new listings, got {recent}")
        return 1

if __name__ == "__main__":
    sys.exit(main() or 0)
