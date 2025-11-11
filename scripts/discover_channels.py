#!/usr/bin/env python3
"""
Post a test message to each channel to discover their IDs
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot
from configs.settings import settings


async def discover_channels():
    """Post test messages and get channel IDs from updates"""
    
    print("=" * 60)
    print("🔍 Discovering Channel IDs")
    print("=" * 60)
    print()
    
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    
    try:
        # Get bot info
        me = await bot.get_me()
        print(f"✅ Bot: @{me.username}")
        print(f"   Token configured: {settings.TELEGRAM_BOT_TOKEN[:20]}...")
        print()
        
        print("📱 Fetching recent updates...")
        
        # Get recent updates (last 100)
        updates = await bot.get_updates(limit=100, offset=-1)
        
        channels_found = {}
        
        if updates:
            print(f"✅ Found {len(updates)} updates")
            print()
            
            for update in updates:
                # Check for channel posts
                if update.channel_post:
                    chat = update.channel_post.chat
                    if chat.id not in channels_found:
                        channels_found[chat.id] = {
                            'title': chat.title,
                            'username': chat.username,
                            'type': chat.type
                        }
        
        if channels_found:
            print("📋 Channels where bot is admin:")
            print()
            
            for idx, (chat_id, info) in enumerate(channels_found.items(), 1):
                print(f"{idx}. {info['title']}")
                print(f"   Channel ID: {chat_id}")
                print(f"   Username: @{info['username'] or 'None'}")
                print()
            
            print("=" * 60)
            print("📝 Update your .env file:")
            print("=" * 60)
            print()
            
            channel_ids = list(channels_found.keys())
            
            if len(channel_ids) >= 3:
                print(f"TELEGRAM_PUBLIC_CHANNEL={channel_ids[0]}")
                print(f"TELEGRAM_PREMIUM_CHANNEL={channel_ids[1]}")
                print(f"TELEGRAM_VIP_CHANNEL={channel_ids[2]}")
            elif len(channel_ids) == 1:
                print(f"# Using same channel for all tiers:")
                print(f"TELEGRAM_PUBLIC_CHANNEL={channel_ids[0]}")
                print(f"TELEGRAM_PREMIUM_CHANNEL={channel_ids[0]}")
                print(f"TELEGRAM_VIP_CHANNEL={channel_ids[0]}")
            else:
                for i, chat_id in enumerate(channel_ids):
                    print(f"TELEGRAM_CHANNEL_{i+1}={chat_id}")
            
            print()
            
        else:
            print("⚠️  No channel posts found in recent updates")
            print()
            print("📝 To discover channel IDs:")
            print("1. Post a message in EACH of your 3 channels")
            print("2. Wait 10 seconds")
            print("3. Run this script again")
            print()
            print("OR use the manual method:")
            print("1. Forward a message from each channel to @userinfobot")
            print("2. It will reply with the channel ID")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(discover_channels())
