"""
Get Telegram Channel IDs using Bot API
This script helps you get channel IDs for private Telegram channels
"""
import os
import sys
import asyncio
import json
from dotenv import load_dotenv
from aiogram import Bot

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env")
    sys.exit(1)

print("=" * 60)
print("🔍 Telegram Channel ID Finder")
print("=" * 60)
print()
print(f"Bot Token: {BOT_TOKEN[:20]}...")
print()
print("📋 Instructions:")
print()
print("1. Create your private channel in Telegram")
print("2. Add @carscout_bg_bot as admin with 'Post Messages' permission")
print("3. POST A TEST MESSAGE in the channel (e.g., 'Test from admin')")
print("4. Run this script - it will show you the channel ID")
print()
print("=" * 60)
print()


async def get_channel_ids():
    """Get channel IDs from bot updates"""
    bot = Bot(token=BOT_TOKEN)
    
    try:
        # Get updates
        updates = await bot.get_updates(offset=-100, limit=100)
        
        if not updates:
            print("❌ No updates found!")
            print()
            print("📝 Make sure you:")
            print("1. Added the bot as admin to your channels")
            print("2. Posted a test message in each channel")
            print("3. Wait a few seconds and try again")
            return
        
        print(f"✅ Found {len(updates)} recent updates")
        print()
        
        # Find channel posts
        channels = {}
        
        for update in updates:
            if update.channel_post:
                post = update.channel_post
                chat = post.chat
                
                channel_id = chat.id
                channel_title = chat.title or "Unknown Channel"
                message_text = post.text or post.caption or "[Media]"
                
                if channel_id not in channels:
                    channels[channel_id] = {
                        "title": channel_title,
                        "messages": []
                    }
                
                channels[channel_id]["messages"].append(message_text[:50])
        
        if not channels:
            print("❌ No channel posts found in recent updates")
            print()
            print("📝 Make sure you posted a message in your channels")
            return
        
        print("=" * 60)
        print("📺 FOUND CHANNELS:")
        print("=" * 60)
        print()
        
        for channel_id, info in channels.items():
            print(f"📢 Channel: {info['title']}")
            print(f"   ID: {channel_id}")
            print(f"   Recent messages: {len(info['messages'])}")
            print(f"   Last message: {info['messages'][-1]}")
            print()
        
        print("=" * 60)
        print("📝 UPDATE YOUR .env FILE:")
        print("=" * 60)
        print()
        
        for channel_id, info in channels.items():
            title = info['title'].lower()
            
            if "premium" in title:
                print(f"TELEGRAM_PREMIUM_CHANNEL={channel_id}")
            elif "vip" in title:
                print(f"TELEGRAM_VIP_CHANNEL={channel_id}")
            elif "public" in title or "deals" in title:
                # Check if it's a public channel (positive ID or @username)
                if channel_id > 0:
                    print(f"# Note: This might be a public channel")
                    print(f"TELEGRAM_PUBLIC_CHANNEL={channel_id}")
                else:
                    print(f"TELEGRAM_PUBLIC_CHANNEL={channel_id}")
            else:
                print(f"# {info['title']}")
                print(f"TELEGRAM_CHANNEL={channel_id}")
            print()
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Make sure:")
        print("1. Bot token is correct in .env")
        print("2. Bot is admin in your channels")
        print("3. You posted messages in the channels")
    
    finally:
        await bot.session.close()


async def get_raw_updates():
    """Get raw JSON updates for manual inspection"""
    bot = Bot(token=BOT_TOKEN)
    
    try:
        updates = await bot.get_updates(offset=-100, limit=100)
        
        print("=" * 60)
        print("📄 RAW JSON (for debugging):")
        print("=" * 60)
        print()
        
        # Convert to dict for pretty printing
        updates_dict = []
        for update in updates:
            if update.channel_post:
                updates_dict.append({
                    "update_id": update.update_id,
                    "channel_post": {
                        "message_id": update.channel_post.message_id,
                        "chat": {
                            "id": update.channel_post.chat.id,
                            "title": update.channel_post.chat.title,
                            "type": update.channel_post.chat.type,
                        },
                        "date": update.channel_post.date,
                        "text": update.channel_post.text or update.channel_post.caption
                    }
                })
        
        print(json.dumps({"ok": True, "result": updates_dict}, indent=2))
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await bot.session.close()


async def main():
    """Main function"""
    choice = input("Choose option:\n1. Get channel IDs (recommended)\n2. Show raw JSON\n\nChoice (1 or 2): ").strip()
    
    print()
    
    if choice == "2":
        await get_raw_updates()
    else:
        await get_channel_ids()
    
    print()
    print("=" * 60)
    print("✅ Done!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
