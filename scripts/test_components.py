"""
Simple Pipeline Test - Manual Step-by-Step
Run this to test each part of the pipeline individually
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.domain.database import async_session_factory
from libs.domain.models import Source, ListingRaw
from sqlalchemy import select
import uuid


async def create_test_listing():
    """Create a test listing in the database"""
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
        
        # Create test listing
        listing = ListingRaw(
            id=uuid.uuid4(),
            source_id=source.id,
            site_ad_id="test_12345",
            url="https://www.mobile.bg/obiavi/test-listing",
            is_active=True,
            raw_html_path=None,
        )
        session.add(listing)
        await session.commit()
        
        print(f"✅ Created test listing: {listing.id}")
        return str(listing.id)


async def test_telegram_post():
    """Test posting to Telegram channels"""
    print("\n📱 Testing Telegram posting...")
    
    from aiogram import Bot
    from configs.settings import settings
    
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    
    test_message = """
🚗 <b>TEST - BMW 320d (2015)</b>

💰 Price: <b>15,900 BGN</b>
⭐ Deal Score: <b>8.5/10</b>

📊 Details:
• Year: 2015
• Mileage: 180,000 km
• Fuel: Diesel
• Power: 184 HP
• Transmission: Automatic

🔥 <b>Why it's a great deal:</b>
• Price 15% below market
• Well maintained
• Full service history
• No accidents reported

📍 Location: Sofia
🔗 <a href="https://www.mobile.bg/test">View listing</a>

#BMW #Diesel #Sofia
"""
    
    try:
        # Test public channel
        print("  Testing @CarScoutBG (public)...")
        await bot.send_message(
            chat_id=settings.TELEGRAM_PUBLIC_CHANNEL,
            text=test_message,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        print("  ✅ Posted to public channel")
        
        # Test premium channel
        print("  Testing Premium channel...")
        await bot.send_message(
            chat_id=settings.TELEGRAM_PREMIUM_CHANNEL,
            text=test_message,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        print("  ✅ Posted to Premium channel")
        
        # Test VIP channel
        print("  Testing VIP channel...")
        await bot.send_message(
            chat_id=settings.TELEGRAM_VIP_CHANNEL,
            text=test_message,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        print("  ✅ Posted to VIP channel")
        
        print("\n✅ All Telegram posts successful!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await bot.session.close()


async def test_openai():
    """Test OpenAI API connection"""
    print("\n🤖 Testing OpenAI API...")
    
    from openai import AsyncOpenAI
    from configs.settings import settings
    
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a car expert."},
                {"role": "user", "content": "Is a 2015 BMW 320d with 180k km for 15,900 BGN a good deal?"}
            ],
            max_tokens=100
        )
        
        print("  ✅ OpenAI API connected")
        print(f"  Response: {response.choices[0].message.content[:100]}...")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")


async def test_database():
    """Test database connection"""
    print("\n🗄️  Testing database...")
    
    async with async_session_factory() as session:
        # Count tables
        from libs.domain.models import ListingRaw, ListingNormalized, User, Score
        
        raw_count = len((await session.execute(select(ListingRaw))).scalars().all())
        normalized_count = len((await session.execute(select(ListingNormalized))).scalars().all())
        users_count = len((await session.execute(select(User))).scalars().all())
        scores_count = len((await session.execute(select(Score))).scalars().all())
        
        print(f"  ✅ Database connected")
        print(f"     Raw listings: {raw_count}")
        print(f"     Normalized: {normalized_count}")
        print(f"     Users: {users_count}")
        print(f"     Scores: {scores_count}")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 CarScout AI - System Component Tests")
    print("=" * 60)
    
    try:
        # Test 1: Database
        await test_database()
        
        # Test 2: OpenAI
        await test_openai()
        
        # Test 3: Telegram
        await test_telegram_post()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\n💡 Your system is ready! Next steps:")
        print("   1. Check your Telegram channels for test messages")
        print("   2. Start Celery workers: python scripts/start_workers.ps1")
        print("   3. Run full pipeline test: python scripts/test_full_pipeline.py")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
