"""
Simple Scrape Test - Get a few real listings from Mobile.bg
This script will:
1. Scrape 10 listings from Mobile.bg
2. Process them through the pipeline
3. Post the best deals to your Telegram channels
"""
import sys
import os
import asyncio
import time
from datetime import datetime, timezone
from uuid import UUID

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.domain.database import async_session_factory
from libs.domain.models import Source, ListingRaw, ListingNormalized, Score
from sqlalchemy import select
import uuid


async def setup_source():
    """Ensure Mobile.bg source exists"""
    print("🔧 Setting up Mobile.bg source...")
    
    async with async_session_factory() as session:
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
                crawl_interval_s=3600,
            )
            session.add(source)
            await session.commit()
            print(f"✅ Created source: {source.id}")
        else:
            print(f"✅ Source exists: {source.id}")
        
        return source


async def create_sample_listings(source):
    """Create sample test listings to process"""
    print("\n📝 Creating sample test listings...")
    print("   (In production, these would come from actual scraping)")
    
    sample_listings = [
        {
            "site_ad_id": "sample_001",
            "url": "https://www.mobile.bg/sample/bmw-320d-2015",
            "title": "BMW 320d - 2015",
            "year": 2015,
            "price": 15900,
            "mileage": 180000,
        },
        {
            "site_ad_id": "sample_002", 
            "url": "https://www.mobile.bg/sample/vw-golf-2018",
            "title": "VW Golf VII - 2018",
            "year": 2018,
            "price": 18500,
            "mileage": 95000,
        },
        {
            "site_ad_id": "sample_003",
            "url": "https://www.mobile.bg/sample/audi-a4-2016",
            "title": "Audi A4 - 2016",
            "year": 2016,
            "price": 21500,
            "mileage": 145000,
        },
    ]
    
    created_ids = []
    async with async_session_factory() as session:
        for listing_data in sample_listings:
            # Check if already exists
            result = await session.execute(
                select(ListingRaw).where(
                    ListingRaw.source_id == source.id,
                    ListingRaw.site_ad_id == listing_data["site_ad_id"]
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                listing = ListingRaw(
                    id=uuid.uuid4(),
                    source_id=source.id,
                    site_ad_id=listing_data["site_ad_id"],
                    url=listing_data["url"],
                    is_active=True,
                    first_seen_at=datetime.now(),
                    last_seen_at=datetime.now(),
                    raw_html_path=None,
                )
                session.add(listing)
                created_ids.append(str(listing.id))
                print(f"  ✅ Created: {listing_data['title']}")
            else:
                created_ids.append(str(existing.id))
                print(f"  ℹ️  Exists: {listing_data['title']}")
        
        await session.commit()
    
    return created_ids


async def process_listings(listing_ids):
    """Process listings through the pipeline"""
    print(f"\n⚙️  Processing {len(listing_ids)} listings through pipeline...")
    print("=" * 60)
    
    from workers.pipeline.tasks.parse import parse_listing
    from workers.pipeline.tasks.normalize import normalize_listing
    from workers.pipeline.tasks.dedupe import deduplicate_listing
    from workers.pipeline.tasks.price import estimate_price
    from workers.pipeline.tasks.ai import classify_risk, llm_evaluate
    from workers.pipeline.tasks.score import calculate_score
    from workers.pipeline.tasks.notify import post_to_channel
    from libs.domain.database import get_sync_session
    
    results = []
    
    for i, listing_id in enumerate(listing_ids, 1):
        print(f"\n[{i}/{len(listing_ids)}] Processing listing {listing_id[:8]}...")
        
        try:
            # Step 1: Parse (will trigger normalize automatically)
            print("  1️⃣  Parsing (will auto-trigger normalize)...")
            parse_result = parse_listing.delay(listing_id)
            parse_data = parse_result.get(timeout=10)
            
            if not parse_data:
                print("  ❌ Parse failed")
                continue
            
            print(f"  ✅ Parsed: {parse_data}")
            
            # Wait a bit for normalize to complete (it's triggered automatically)
            print("  2️⃣  Waiting for normalization...")
            import time
            time.sleep(2)
            
            # Get the normalized listing ID from database
            from libs.domain.models import ListingNormalized
            from libs.domain.database import get_sync_session
            session = get_sync_session()
            normalized = session.query(ListingNormalized).filter_by(
                raw_id=UUID(listing_id)
            ).first()
            session.close()
            
            if not normalized:
                print("  ❌ Normalization failed")
                continue
            
            normalized_id = str(normalized.id)
            print(f"  ✅ Normalized ID: {normalized_id[:8]}")
            
            # Step 3: Wait for dedupe (triggered automatically by normalize)
            print("  3️⃣  Waiting for deduplication...")
            time.sleep(2)
            
            # Check if marked as duplicate
            session = get_sync_session()
            normalized = session.query(ListingNormalized).filter_by(id=UUID(normalized_id)).first()
            session.close()
            
            if normalized and normalized.is_duplicate:
                print("  ⚠️  Duplicate detected - skipping")
                continue
            
            # Step 4-8: Trigger price estimation, which auto-chains to the rest
            # Pipeline: price → classify_risk → llm_evaluate → calculate_score → post_to_channel
            print("  4️⃣  Starting pipeline (price → risk → AI → score → post)...")
            
            # Trigger the price estimation (first task in chain)
            price_result = estimate_price.delay(normalized_id)
            
            # Wait for price estimation to complete
            print("     ⏳ Estimating price...")
            price_data = price_result.get(timeout=20)
            print(f"     ✅ Price: {price_data.get('predicted_price', 0):.0f} BGN (discount: {price_data.get('discount_pct', 0):.1f}%)")
            
            # Now wait for the full chain to complete by checking the score
            # The chain is: classify_risk → llm_evaluate → calculate_score
            print("     ⏳ Running AI evaluation (this takes ~10 seconds)...")
            time.sleep(12)  # Give OpenAI time to respond
            
            # Check if score was calculated
            session = get_sync_session()
            score_record = session.query(Score).filter_by(listing_id=UUID(normalized_id)).first()
            session.close()
            
            if score_record:
                print(f"  ⭐ Score: {score_record.score:.1f}/10 (state: {score_record.final_state})")
                
                results.append({
                    'id': normalized_id,
                    'score': score_record.score,
                    'state': score_record.final_state,
                })
                
                # Check if it was posted to channels
                if score_record.final_state == 'approved':
                    print("  📱 Status: Approved for channel posting")
                else:
                    print(f"  ⏭️  Status: {score_record.final_state} (not posted)")
            else:
                print("  ⚠️  Score not yet calculated (chain still running)")
            
            print("  ✅ Complete!")
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    return results


async def show_summary(results):
    """Show processing summary"""
    print("\n" + "=" * 60)
    print("📊 PROCESSING SUMMARY")
    print("=" * 60)
    
    if not results:
        print("❌ No listings were successfully processed")
        return
    
    approved = [r for r in results if r['state'] == 'approved']
    rejected = [r for r in results if r['state'] == 'rejected']
    draft = [r for r in results if r['state'] == 'draft']
    
    print(f"✅ Approved: {len(approved)}")
    print(f"❌ Rejected: {len(rejected)}")
    print(f"📝 Draft: {len(draft)}")
    print(f"\nAverage Score: {sum(r['score'] for r in results) / len(results):.1f}/10")
    
    if approved:
        print(f"\n🏆 Top Deals (Approved):")
        for r in sorted(approved, key=lambda x: x['score'], reverse=True)[:3]:
            print(f"  • Score: {r['score']:.1f}/10 (ID: {r['id'][:8]}...)")
    
    print("\n" + "=" * 60)


async def main():
    print("=" * 60)
    print("🚀 CarScout AI - Simple Scrape Test")
    print("=" * 60)
    print(f"⏰ Started: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
    try:
        # Step 1: Setup source
        source = await setup_source()
        
        # Step 2: Create sample listings
        listing_ids = await create_sample_listings(source)
        
        # Step 3: Process listings
        results = await process_listings(listing_ids)
        
        # Step 4: Show summary
        await show_summary(results)
        
        print("\n✅ TEST COMPLETE!")
        print("\n💡 Next steps:")
        print("   1. Check your Telegram channels for posted listings")
        print("   2. Review the database for detailed results:")
        print("      docker exec -it carscout-postgres psql -U carscout -d carscout_ai")
        print("   3. To run a real scrape, use: scrapy crawl mobile_bg")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
