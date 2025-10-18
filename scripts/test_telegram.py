#!/usr/bin/env python3
"""
Test Telegram Bot Integration
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configs.settings import settings

async def test_telegram():
    print("🤖 Testing Telegram Bot Integration")
    print("=" * 60)
    print()
    
    # Check if bot token is configured
    if not settings.TELEGRAM_BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Telegram bot token not configured")
        print()
        print("To set up:")
        print("1. Talk to @BotFather on Telegram")
        print("2. Create a new bot with /newbot")
        print("3. Copy the token to .env file:")
        print("   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHI...")
        print()
        print("See TELEGRAM-SETUP.md for full instructions")
        return 1
    
    print(f"✅ Bot Token: {settings.TELEGRAM_BOT_TOKEN[:20]}...{settings.TELEGRAM_BOT_TOKEN[-10:]}")
    print()
    
    try:
        from aiogram import Bot
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        
        print("🔄 Connecting to Telegram API...")
        print()
        
        # Get bot info
        me = await bot.get_me()
        
        print("✅ Bot connected successfully!")
        print()
        print(f"Bot Details:")
        print(f"  Username: @{me.username}")
        print(f"  Name: {me.first_name}")
        print(f"  ID: {me.id}")
        print(f"  Can join groups: {me.can_join_groups}")
        print(f"  Can read messages: {me.can_read_all_group_messages}")
        print()
        
        # Check webhook status
        webhook_info = await bot.get_webhook_info()
        
        if webhook_info.url:
            print(f"⚙️  Webhook Mode:")
            print(f"  URL: {webhook_info.url}")
            print(f"  Pending updates: {webhook_info.pending_update_count}")
        else:
            print("⚙️  Polling Mode (no webhook set)")
        
        print()
        print("=" * 60)
        print("✅ Telegram integration test PASSED")
        print()
        print("Next steps:")
        print("  1. Start your bot: python3 -m apps.bot.main")
        print("  2. Open Telegram and search: @" + me.username)
        print("  3. Send /start to your bot")
        print("  4. Try creating an alert with /watch")
        print()
        print("See TELEGRAM-SETUP.md for complete guide")
        
        await bot.session.close()
        return 0
        
    except ImportError:
        print("❌ aiogram package not installed")
        print("Install with: pip install aiogram")
        return 1
    except Exception as e:
        print(f"❌ Telegram API test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(test_telegram()))
