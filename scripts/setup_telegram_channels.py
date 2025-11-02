#!/usr/bin/env python3
"""
Setup script for Telegram channels and bots
Tests bot connections and helps create channels
"""

import asyncio
import os
from aiogram import Bot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_bot(bot_token: str, bot_name: str) -> dict:
    """Test bot connection and get bot info"""
    try:
        bot = Bot(token=bot_token)
        bot_info = await bot.get_me()
        await bot.session.close()
        
        return {
            "success": True,
            "name": bot_name,
            "username": bot_info.username,
            "id": bot_info.id,
            "first_name": bot_info.first_name
        }
    except Exception as e:
        return {
            "success": False,
            "name": bot_name,
            "error": str(e)
        }

async def main():
    """Test all bot connections"""
    
    print("=" * 60)
    print("🤖 CarScout AI - Telegram Bot Setup")
    print("=" * 60)
    print()
    
    # Get bot tokens from .env
    main_token = os.getenv("TELEGRAM_BOT_TOKEN")
    premium_token = os.getenv("TELEGRAM_PREMIUM_BOT_TOKEN")
    vip_token = os.getenv("TELEGRAM_VIP_BOT_TOKEN")
    
    bots = [
        (main_token, "Main Bot"),
        (premium_token, "Premium Bot"),
        (vip_token, "VIP Bot")
    ]
    
    print("Testing bot connections...\n")
    
    results = []
    for token, name in bots:
        if not token or token == "YOUR_BOT_TOKEN_HERE":
            print(f"❌ {name}: Not configured")
            continue
        
        result = await test_bot(token, name)
        results.append(result)
        
        if result["success"]:
            print(f"✅ {result['name']}")
            print(f"   Username: @{result['username']}")
            print(f"   Bot ID: {result['id']}")
            print(f"   Name: {result['first_name']}")
        else:
            print(f"❌ {result['name']}")
            print(f"   Error: {result['error']}")
        print()
    
    print("=" * 60)
    print()
    
    # Check if all bots are working
    all_working = all(r["success"] for r in results)
    
    if all_working:
        print("✅ All bots are working!")
        print()
        print("📋 Next Steps:")
        print()
        print("1️⃣  CREATE PUBLIC CHANNEL (FREE users)")
        print("   • Open Telegram → New Channel")
        print("   • Name: 'CarScout Deals'")
        print("   • Username: @CarScoutDeals (or similar)")
        print("   • Make it PUBLIC")
        print(f"   • Add @{results[0]['username']} as admin")
        print("   • Give 'Post Messages' permission")
        print()
        print("2️⃣  CREATE PREMIUM CHANNEL (€14.99/mo)")
        print("   • Open Telegram → New Channel")
        print("   • Name: 'CarScout Premium'")
        print("   • Make it PRIVATE (no username)")
        print(f"   • Add @{results[1]['username']} as admin")
        print("   • Add @RawDataBot to get channel ID")
        print("   • Copy the chat ID (like: -1001234567890)")
        print("   • Remove @RawDataBot")
        print()
        print("3️⃣  CREATE VIP CHANNEL (€29.99/mo)")
        print("   • Open Telegram → New Channel")
        print("   • Name: 'CarScout VIP'")
        print("   • Make it PRIVATE (no username)")
        print(f"   • Add @{results[2]['username']} as admin")
        print("   • Add @RawDataBot to get channel ID")
        print("   • Copy the chat ID (like: -1009876543210)")
        print("   • Remove @RawDataBot")
        print()
        print("4️⃣  UPDATE .env FILE")
        print("   • TELEGRAM_PUBLIC_CHANNEL=@CarScoutDeals")
        print("   • TELEGRAM_PREMIUM_CHANNEL=-1001234567890")
        print("   • TELEGRAM_VIP_CHANNEL=-1009876543210")
        print()
        print("5️⃣  TEST POSTING")
        print("   • Run: python scripts/test_channel_posting.py")
        print()
    else:
        print("❌ Some bots are not working!")
        print()
        print("🔧 Troubleshooting:")
        print("   1. Check if bot tokens are correct in .env")
        print("   2. Make sure tokens don't have extra spaces")
        print("   3. Generate new tokens from @BotFather if needed")
        print()
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
