"""
Live monitor: Wait for channel posts in real-time
This script will continuously check for new updates
"""
import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

print("=" * 70)
print("👀 Live Channel Monitor - Waiting for Posts...")
print("=" * 70)
print()
print("This script will check for new channel posts every 3 seconds.")
print()
print("📝 ACTION NOW:")
print("   1. Make sure privacy mode is DISABLED in @BotFather")
print("   2. Go to your channels")
print("   3. Post a message (e.g., 'Test 2' or 'Hello')")
print("   4. Watch this screen - it will show the channel ID!")
print()
print("Press Ctrl+C to stop")
print()
print("=" * 70)
print()

url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
last_update_id = 0
found_channels = {}

try:
    while True:
        # Get updates
        params = {"offset": last_update_id + 1, "timeout": 30}
        response = requests.get(url, params=params, timeout=35)
        data = response.json()
        
        if not data.get("ok"):
            print(f"❌ API Error: {data}")
            time.sleep(3)
            continue
        
        updates = data.get("result", [])
        
        if updates:
            for update in updates:
                last_update_id = max(last_update_id, update["update_id"])
                
                # Check for channel posts
                if "channel_post" in update:
                    post = update["channel_post"]
                    chat = post["chat"]
                    
                    channel_id = chat["id"]
                    channel_title = chat.get("title", "Unknown")
                    channel_type = chat.get("type", "unknown")
                    username = chat.get("username")
                    message = post.get("text") or post.get("caption") or "[Media]"
                    
                    if channel_id not in found_channels:
                        found_channels[channel_id] = {
                            "title": channel_title,
                            "username": username,
                            "type": channel_type
                        }
                        
                        print("=" * 70)
                        print(f"🎉 NEW CHANNEL DETECTED!")
                        print("=" * 70)
                        print(f"📢 Channel: {channel_title}")
                        print(f"   ID: {channel_id}")
                        print(f"   Type: {channel_type}")
                        if username:
                            print(f"   Username: @{username}")
                        print(f"   Message: {message[:60]}")
                        print()
                        
                        # Show .env config
                        title_lower = channel_title.lower()
                        if "premium" in title_lower:
                            print(f"   💾 Add to .env:")
                            print(f"   TELEGRAM_PREMIUM_CHANNEL={channel_id}")
                        elif "vip" in title_lower:
                            print(f"   💾 Add to .env:")
                            print(f"   TELEGRAM_VIP_CHANNEL={channel_id}")
                        elif username:
                            print(f"   💾 Add to .env:")
                            print(f"   TELEGRAM_PUBLIC_CHANNEL=@{username}")
                        else:
                            print(f"   💾 Add to .env:")
                            print(f"   TELEGRAM_CHANNEL={channel_id}")
                        
                        print("=" * 70)
                        print()
                    
                    # Check if we found all channels
                    if len(found_channels) >= 3:
                        print()
                        print("=" * 70)
                        print("✅ ALL CHANNELS FOUND!")
                        print("=" * 70)
                        print()
                        print("📋 Summary:")
                        for ch_id, info in found_channels.items():
                            print(f"   {info['title']}: {ch_id}")
                        print()
                        print("💾 Copy to your .env file:")
                        print()
                        
                        for ch_id, info in found_channels.items():
                            title_lower = info['title'].lower()
                            if "premium" in title_lower:
                                print(f"TELEGRAM_PREMIUM_CHANNEL={ch_id}")
                            elif "vip" in title_lower:
                                print(f"TELEGRAM_VIP_CHANNEL={ch_id}")
                            elif info.get('username'):
                                print(f"TELEGRAM_PUBLIC_CHANNEL=@{info['username']}")
                            else:
                                print(f"# {info['title']}")
                                print(f"CHANNEL={ch_id}")
                        
                        print()
                        print("=" * 70)
                        print()
                        print("Press Ctrl+C to exit")
                
                # Show other update types for debugging
                elif "message" in update:
                    msg = update["message"]
                    chat = msg["chat"]
                    chat_type = chat.get("type")
                    
                    if chat_type == "private":
                        print(f"⚪ Private message from {chat.get('first_name', 'Unknown')}")
                    elif chat_type in ["group", "supergroup"]:
                        print(f"⚪ Group message in {chat.get('title', 'Unknown')}")
        
        # Show progress indicator
        if len(found_channels) == 0:
            print(f"⏳ Waiting for channel posts... (found {len(updates)} updates, 0 channels)", end='\r')
        
        time.sleep(1)  # Check every second

except KeyboardInterrupt:
    print()
    print()
    print("=" * 70)
    print("🛑 Stopped monitoring")
    print("=" * 70)
    
    if found_channels:
        print()
        print(f"✅ Found {len(found_channels)} channel(s):")
        for ch_id, info in found_channels.items():
            print(f"   {info['title']}: {ch_id}")
    else:
        print()
        print("❌ No channels found")
        print()
        print("Make sure:")
        print("   1. Privacy mode is DISABLED in @BotFather")
        print("   2. Bot is ADMIN in your channels")
        print("   3. You posted messages IN the channels")
    
    print()

except Exception as e:
    print()
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
