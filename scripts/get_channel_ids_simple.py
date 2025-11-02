"""
Quick test: Verify bot token and get channel IDs using Telegram Bot API
This is the simplest way - no RawDataBot needed!
"""
import os
import requests
import json
from dotenv import load_dotenv

# Load .env
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not found in .env")
    exit(1)

print("=" * 70)
print("🔍 Telegram Bot API - Get Channel IDs")
print("=" * 70)
print()
print(f"✅ Bot Token: {BOT_TOKEN[:20]}...")
print()

# API URL
url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

print(f"📡 Calling: {url}")
print()

try:
    # Make request
    response = requests.get(url)
    data = response.json()
    
    if not data.get("ok"):
        print("❌ API Error:")
        print(json.dumps(data, indent=2))
        exit(1)
    
    updates = data.get("result", [])
    
    if not updates:
        print("⚠️  No updates found!")
        print()
        print("📝 To get channel IDs:")
        print("1. Create your channels in Telegram")
        print("2. Add @carscout_bg_bot as admin")
        print("3. POST A TEST MESSAGE in each channel")
        print("4. Run this script again")
        print()
        exit(0)
    
    print(f"✅ Found {len(updates)} updates")
    print()
    print("=" * 70)
    
    # Find channel posts
    channels = {}
    
    for update in updates:
        if "channel_post" in update:
            post = update["channel_post"]
            chat = post["chat"]
            
            channel_id = chat["id"]
            channel_title = chat.get("title", "Unknown")
            message = post.get("text") or post.get("caption") or "[Media]"
            
            if channel_id not in channels:
                channels[channel_id] = {
                    "title": channel_title,
                    "type": chat.get("type"),
                    "messages": []
                }
            
            channels[channel_id]["messages"].append(message[:60])
    
    if not channels:
        print("⚠️  No channel posts found")
        print()
        print("Make sure you posted messages in your channels!")
        exit(0)
    
    # Display results
    print("📺 YOUR CHANNELS:")
    print("=" * 70)
    print()
    
    for channel_id, info in channels.items():
        print(f"Channel: {info['title']}")
        print(f"ID:      {channel_id}")
        print(f"Type:    {info['type']}")
        print(f"Posts:   {len(info['messages'])}")
        if info['messages']:
            print(f"Latest:  {info['messages'][-1]}")
        print()
    
    print("=" * 70)
    print("📋 COPY TO YOUR .env FILE:")
    print("=" * 70)
    print()
    
    # Generate .env lines
    for channel_id, info in channels.items():
        title_lower = info['title'].lower()
        
        if "premium" in title_lower:
            print(f"TELEGRAM_PREMIUM_CHANNEL={channel_id}")
        elif "vip" in title_lower:
            print(f"TELEGRAM_VIP_CHANNEL={channel_id}")
        else:
            # Might be public channel
            if channel_id < 0:
                print(f"# {info['title']}")
                print(f"TELEGRAM_CHANNEL={channel_id}")
            else:
                print(f"# Public channel (use @username instead)")
                print(f"# TELEGRAM_PUBLIC_CHANNEL=@YourChannelUsername")
        print()
    
    print("=" * 70)
    print()
    print("✅ Done! Copy the IDs above to your .env file")
    print()
    
except requests.exceptions.RequestException as e:
    print(f"❌ Network Error: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
