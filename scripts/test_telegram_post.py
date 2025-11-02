"""
Super Simple Test - Just post to Telegram
Creates a listing and posts it to all channels
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot
from configs.settings import settings


async def post_test_listing():
    """Post a test car listing to all channels"""
    print("=" * 60)
    print("🚀 Posting Test Listing to Telegram Channels")
    print("=" * 60)
    
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    
    message = """
🚗 <b>BMW 320d xDrive (2015)</b> - TEST POSTING

💰 Price: <b>15,900 BGN</b>
⭐ Deal Score: <b>8.5/10</b>

📊 Details:
• Year: 2015
• Mileage: 180,000 km
• Fuel: Diesel
• Power: 184 HP
• Transmission: Automatic
• Body: Sedan

🔥 <b>Why it's a great deal:</b>
• Price 15% below market average
• Full service history
• Well maintained
• No accidents reported

💡 <b>Market Analysis:</b>
• Predicted fair price: 18,500 BGN
• You save: 2,600 BGN (14% discount)
• Similar cars: 45 found

📍 Location: Sofia
🔗 View full listing

<i>🤖 This is a test post from CarScout AI</i>
#Test #BMW #Diesel #Sofia #GreatDeal
"""
    
    try:
        # Post to Public channel
        print("\n📱 Posting to Public channel (@CarScoutBG)...")
        msg1 = await bot.send_message(
            chat_id=settings.TELEGRAM_PUBLIC_CHANNEL,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        print(f"  ✅ Posted! Message ID: {msg1.message_id}")
        
        # Post to Premium channel
        print("\n📱 Posting to Premium channel...")
        msg2 = await bot.send_message(
            chat_id=settings.TELEGRAM_PREMIUM_CHANNEL,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        print(f"  ✅ Posted! Message ID: {msg2.message_id}")
        
        # Post to VIP channel
        print("\n📱 Posting to VIP channel...")
        msg3 = await bot.send_message(
            chat_id=settings.TELEGRAM_VIP_CHANNEL,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        print(f"  ✅ Posted! Message ID: {msg3.message_id}")
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Test listing posted to all channels!")
        print("=" * 60)
        print("\n📱 Check your Telegram channels:")
        print(f"   • Public: @CarScoutBG")
        print(f"   • Premium: {settings.TELEGRAM_PREMIUM_CHANNEL}")
        print(f"   • VIP: {settings.TELEGRAM_VIP_CHANNEL}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(post_test_listing())
