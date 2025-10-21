"""
Direct Test - No Celery Required
Tests the pipeline functions directly without using Celery workers
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.domain.database import async_session_factory, sync_session_factory
from libs.domain.models import Source, ListingRaw, ListingNormalized, Score
from libs.domain.scoring import calculate_deal_score
from sqlalchemy import select
import uuid
from aiogram import Bot
from configs.settings import settings


async def create_test_listing():
    """Create a normalized test listing directly"""
    print("📝 Creating test listing...")
    
    async with async_session_factory() as session:
        # Create source if not exists
        result = await session.execute(select(Source).where(Source.name == "Mobile.bg"))
        source = result.scalar_one_or_none()
        
        if not source:
            source = Source(
                id=uuid.uuid4(),
                name="Mobile.bg",
                base_url="https://www.mobile.bg",
                enabled=True,
            )
            session.add(source)
            await session.flush()
        
        # Create raw listing
        raw = ListingRaw(
            id=uuid.uuid4(),
            source_id=source.id,
            site_ad_id="direct_test_001",
            url="https://www.mobile.bg/direct-test",
            is_active=True,
        )
        session.add(raw)
        await session.flush()
        
        # Create normalized listing with realistic data
        normalized = ListingNormalized(
            id=uuid.uuid4(),
            raw_id=raw.id,
            brand_id="BMW",
            model_id="320d",
            year=2015,
            mileage_km=180000,
            fuel="Diesel",
            gearbox="Automatic",
            body="Sedan",
            price_bgn=15900,
            currency="BGN",
            region="Sofia",
            title="BMW 320d xDrive - 2015",
            description="Excellent condition, full service history, leather interior, navigation",
            is_duplicate=False,
        )
        session.add(normalized)
        await session.commit()
        
        print(f"✅ Created listing: {normalized.id}")
        return normalized.id


async def test_scoring(listing_id):
    """Test the scoring function"""
    print("\n⭐ Testing scoring system...")
    
    async with async_session_factory() as session:
        result = await session.execute(
            select(ListingNormalized).where(ListingNormalized.id == listing_id)
        )
        listing = result.scalar_one()
        
        # Use sync session for scoring (it expects sync)
        with sync_session_factory() as sync_session:
            sync_result = sync_session.execute(
                select(ListingNormalized).where(ListingNormalized.id == listing_id)
            )
            sync_listing = sync_result.scalar_one()
            
            # Calculate score
            score_data = calculate_deal_score(
                listing=sync_listing,
                predicted_price=17500,  # Simulated ML prediction
                market_p10=14000,
                market_p50=17500,
                market_p90=21000,
                risk_level="low",
                sample_size=50,
            )
            
            # Save score
            score = Score(
                id=uuid.uuid4(),
                listing_id=listing_id,
                score=score_data["score"],
                reasons=score_data["reasons"],
                final_state=score_data["final_state"],
            )
            sync_session.add(score)
            sync_session.commit()
            
            print(f"  Score: {score_data['score']:.1f}/10")
            print(f"  State: {score_data['final_state']}")
            print(f"  Reasons: {', '.join(score_data['reasons'][:3])}")
            
            return score_data


async def test_telegram_post(listing_id, score_data):
    """Test posting to Telegram"""
    print("\n📱 Testing Telegram posting...")
    
    async with async_session_factory() as session:
        result = await session.execute(
            select(ListingNormalized).where(ListingNormalized.id == listing_id)
        )
        listing = result.scalar_one()
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        
        # Determine which channels based on score
        channels = []
        if score_data["score"] >= 9.0:
            channels = ["Public", "Premium", "VIP"]
        elif score_data["score"] >= 7.5:
            channels = ["Premium", "VIP"]
        elif score_data["score"] >= 6.5:
            channels = ["VIP"]
        
        if not channels:
            print("  ⏭️  Score too low for posting")
            await bot.session.close()
            return
        
        # Create message
        message = f"""
🚗 <b>{listing.brand_id} {listing.model_id} ({listing.year})</b>

💰 Price: <b>{listing.price_bgn:,.0f} BGN</b>
⭐ Deal Score: <b>{score_data['score']:.1f}/10</b>

📊 Details:
• Year: {listing.year}
• Mileage: {listing.mileage_km:,} km
• Fuel: {listing.fuel}
• Transmission: {listing.gearbox}
• Body: {listing.body}

🔥 <b>Why it's a great deal:</b>
{chr(10).join(f'• {reason}' for reason in score_data['reasons'][:3])}

📍 Location: {listing.region}
🔗 <a href="{listing.title}">View listing</a>

#Test #DirectPipeline #{listing.brand_id}
"""
        
        # Post to channels
        channel_map = {
            "Public": settings.TELEGRAM_PUBLIC_CHANNEL,
            "Premium": settings.TELEGRAM_PREMIUM_CHANNEL,
            "VIP": settings.TELEGRAM_VIP_CHANNEL,
        }
        
        for channel_name in channels:
            try:
                channel_id = channel_map[channel_name]
                await bot.send_message(
                    chat_id=channel_id,
                    text=message,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
                print(f"  ✅ Posted to {channel_name}")
            except Exception as e:
                print(f"  ❌ Failed to post to {channel_name}: {e}")
        
        await bot.session.close()


async def main():
    print("=" * 60)
    print("🚀 CarScout AI - Direct Pipeline Test")
    print("=" * 60)
    print("   (No Celery workers required)")
    print("=" * 60)
    
    try:
        # Step 1: Create test listing
        listing_id = await create_test_listing()
        
        # Step 2: Test scoring
        score_data = await test_scoring(listing_id)
        
        # Step 3: Test Telegram posting
        await test_telegram_post(listing_id, score_data)
        
        print("\n" + "=" * 60)
        print("✅ TEST COMPLETE!")
        print("=" * 60)
        print("\n💡 What happened:")
        print("   1. Created a normalized listing in the database")
        print("   2. Calculated a deal score using the scoring algorithm")
        print("   3. Posted the listing to appropriate Telegram channels")
        print("\n📱 Check your Telegram channels now!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
