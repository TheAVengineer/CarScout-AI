"""
Quick Pipeline Test - End-to-End System Validation
Scrapes a few listings from Mobile.bg and processes them through the entire pipeline
"""
import sys
import os
import asyncio
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.domain.database import async_engine, async_session_factory
from libs.domain.models import Source, ListingRaw
from sqlalchemy import select
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import uuid


async def setup_mobile_bg_source():
    """Create Mobile.bg source in database if it doesn't exist"""
    print("🔧 Setting up Mobile.bg source...")
    
    async with async_session_factory() as session:
        # Check if source exists
        result = await session.execute(
            select(Source).where(Source.name == "Mobile.bg")
        )
        source = result.scalar_one_or_none()
        
        if not source:
            source = Source(
                id=uuid.uuid4(),
                name="Mobile.bg",
                base_url="https://www.mobile.bg",
                enabled=True,
                crawl_interval_s=3600,  # 1 hour
            )
            session.add(source)
            await session.commit()
            print(f"✅ Created Mobile.bg source: {source.id}")
        else:
            print(f"✅ Mobile.bg source exists: {source.id}")
        
        return source.id


async def check_listings():
    """Check how many listings we have"""
    async with async_session_factory() as session:
        result = await session.execute(select(ListingRaw))
        listings = result.scalars().all()
        print(f"📊 Found {len(listings)} raw listings in database")
        
        for listing in listings[:5]:  # Show first 5
            print(f"  - {listing.url[:60]}... (Active: {listing.is_active})")


def run_scraper():
    """Run Scrapy spider to scrape Mobile.bg"""
    print("\n🕷️  Starting scraper...")
    print("=" * 60)
    
    # Import spider
    from workers.scrape.spiders.mobile_bg import MobileBgSpider
    
    # Configure Scrapy
    settings = get_project_settings()
    settings.update({
        'CLOSESPIDER_PAGECOUNT': 2,  # Only scrape 2 pages (about 40 listings)
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 2,
        'LOG_LEVEL': 'INFO',
        'ITEM_PIPELINES': {
            'workers.scrape.pipelines.DatabasePipeline': 300,
        }
    })
    
    # Run spider
    process = CrawlerProcess(settings)
    process.crawl(MobileBgSpider)
    process.start()
    
    print("=" * 60)
    print("✅ Scraping complete!")


async def process_pipeline():
    """Process listings through the pipeline"""
    print("\n⚙️  Processing pipeline tasks...")
    print("=" * 60)
    
    # Import Celery tasks
    from workers.pipeline.tasks.parse import parse_listing
    from workers.pipeline.tasks.normalize import normalize_listing
    from workers.pipeline.tasks.dedupe import dedupe_listing
    from workers.pipeline.tasks.price import price_listing
    from workers.pipeline.tasks.ai import evaluate_listing
    from workers.pipeline.tasks.score import score_listing
    from workers.pipeline.tasks.notify import notify_listing
    
    # Get all active raw listings
    async with async_session_factory() as session:
        result = await session.execute(
            select(ListingRaw).where(ListingRaw.is_active == True).limit(5)
        )
        listings = result.scalars().all()
        
        print(f"📋 Processing {len(listings)} listings...\n")
        
        for i, listing in enumerate(listings, 1):
            print(f"[{i}/{len(listings)}] Processing: {listing.url[:50]}...")
            
            try:
                # Step 1: Parse
                print("  ├─ 1️⃣ Parsing HTML...")
                parse_result = parse_listing.delay(str(listing.id))
                parse_result.get(timeout=30)
                
                # Step 2: Normalize
                print("  ├─ 2️⃣ Normalizing data...")
                normalize_result = normalize_listing.delay(str(listing.id))
                normalized_id = normalize_result.get(timeout=30)
                
                # Step 3: Dedupe
                print("  ├─ 3️⃣ Checking duplicates...")
                dedupe_result = dedupe_listing.delay(normalized_id)
                dedupe_result.get(timeout=30)
                
                # Step 4: Price prediction
                print("  ├─ 4️⃣ Predicting price...")
                price_result = price_listing.delay(normalized_id)
                price_result.get(timeout=30)
                
                # Step 5: AI evaluation
                print("  ├─ 5️⃣ AI risk analysis...")
                ai_result = evaluate_listing.delay(normalized_id)
                ai_result.get(timeout=30)
                
                # Step 6: Score
                print("  ├─ 6️⃣ Calculating score...")
                score_result = score_listing.delay(normalized_id)
                score_result.get(timeout=30)
                
                # Step 7: Notify (post to channels)
                print("  └─ 7️⃣ Posting to channels...")
                notify_result = notify_listing.delay(normalized_id)
                notify_result.get(timeout=30)
                
                print(f"  ✅ Complete!\n")
                
            except Exception as e:
                print(f"  ❌ Error: {str(e)}\n")
                continue
    
    print("=" * 60)
    print("✅ Pipeline processing complete!")


async def show_results():
    """Show final results"""
    print("\n📊 FINAL RESULTS")
    print("=" * 60)
    
    async with async_session_factory() as session:
        # Count listings by stage
        from libs.domain.models import ListingNormalized, Score, ChannelPost
        
        raw_count = len((await session.execute(select(ListingRaw))).scalars().all())
        normalized_count = len((await session.execute(select(ListingNormalized))).scalars().all())
        scored_count = len((await session.execute(select(Score))).scalars().all())
        posted_count = len((await session.execute(select(ChannelPost))).scalars().all())
        
        print(f"📥 Raw listings scraped:     {raw_count}")
        print(f"🔄 Normalized listings:      {normalized_count}")
        print(f"⭐ Scored listings:          {scored_count}")
        print(f"📢 Posted to channels:       {posted_count}")
        
        # Show top scored listings
        result = await session.execute(
            select(Score, ListingNormalized)
            .join(ListingNormalized, Score.listing_id == ListingNormalized.id)
            .order_by(Score.score.desc())
            .limit(5)
        )
        top_listings = result.all()
        
        if top_listings:
            print(f"\n🏆 TOP 5 DEALS:")
            for i, (score, listing) in enumerate(top_listings, 1):
                print(f"  {i}. Score: {score.score:.1f}/10 - {listing.brand_id} {listing.model_id} ({listing.year})")
                print(f"     Price: {listing.price_bgn:.0f} BGN | State: {score.final_state}")
                
        # Show channel posts
        result = await session.execute(
            select(ChannelPost).order_by(ChannelPost.posted_at.desc()).limit(10)
        )
        posts = result.scalars().all()
        
        if posts:
            print(f"\n📱 POSTED TO CHANNELS:")
            channel_counts = {}
            for post in posts:
                channel_counts[post.channel] = channel_counts.get(post.channel, 0) + 1
            
            for channel, count in channel_counts.items():
                print(f"  {channel}: {count} posts")
    
    print("=" * 60)


async def main():
    """Main test flow"""
    print("=" * 60)
    print("🚀 CarScout AI - Full Pipeline Test")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
    try:
        # Step 1: Setup source
        await setup_mobile_bg_source()
        
        # Step 2: Check existing listings
        await check_listings()
        
        # Step 3: Run scraper
        print("\n⚠️  Starting scraper in 3 seconds...")
        await asyncio.sleep(3)
        run_scraper()
        
        # Step 4: Check listings again
        await check_listings()
        
        # Step 5: Process through pipeline
        input("\n⏸️  Press ENTER to start pipeline processing...")
        await process_pipeline()
        
        # Step 6: Show results
        await show_results()
        
        print("\n" + "=" * 60)
        print("✅ TEST COMPLETE!")
        print("=" * 60)
        print("\n💡 Next steps:")
        print("   1. Check your Telegram channels for posted listings")
        print("   2. Review the database for detailed results")
        print("   3. Adjust scoring thresholds in .env if needed")
        print("   4. Set up Stripe for payment processing")
        print("\n🎉 Your CarScout AI system is working!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
