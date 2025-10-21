"""
Force clear old updates and get fresh channel IDs
Sometimes Telegram caches updates - this script clears them and gets fresh ones
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not found in .env")
    exit(1)

print("=" * 70)
print("🔄 Clearing old updates and fetching fresh channel IDs")
print("=" * 70)
print()

# Step 1: Clear old updates by getting them with a high offset
print("Step 1: Clearing old cached updates...")
url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

try:
    # Get all updates
    response = requests.get(url + "?limit=100")
    data = response.json()
    
    if data.get("ok") and data.get("result"):
        updates = data["result"]
        if updates:
            # Get the last update_id
            last_id = updates[-1]["update_id"]
            print(f"   Found {len(updates)} old updates")
            
            # Clear them by confirming receipt
            clear_url = f"{url}?offset={last_id + 1}"
            requests.get(clear_url)
            print(f"   ✅ Cleared old updates")
        else:
            print("   No old updates to clear")
    
    print()
    
    # Step 2: Get fresh updates (any NEW messages from your channels)
    print("Step 2: Fetching fresh updates...")
    print()
    print("⏳ Waiting for new channel posts...")
    print()
    print("📝 ACTION REQUIRED:")
    print("   1. Go to your Telegram channels")
    print("   2. Post a NEW message (e.g., 'Test 2' or 'Hello')")
    print("   3. Wait 5 seconds")
    print("   4. Press ENTER here")
    print()
    
    input("Press ENTER after posting messages in your channels...")
    print()
    print("🔍 Fetching updates...")
    print()
    
    # Now get fresh updates
    response = requests.get(url + "?limit=100")
    data = response.json()
    
    if not data.get("ok"):
        print("❌ API Error:")
        print(json.dumps(data, indent=2))
        exit(1)
    
    updates = data.get("result", [])
    
    if not updates:
        print("⚠️  Still no updates found!")
        print()
        print("🔍 Troubleshooting:")
        print("   1. Is your bot an ADMIN in the channels?")
        print("   2. Does bot have 'Post Messages' permission?")
        print("   3. Did you post AFTER clearing old updates?")
        print()
        print("Try this:")
        print("   1. Remove bot from channels")
        print("   2. Add bot back as admin")
        print("   3. Post a new test message")
        print("   4. Run this script again")
        print()
        exit(0)
    
    print(f"✅ Found {len(updates)} new updates!")
    print()
    print("=" * 70)
    
    # Parse channel posts
    channels = {}
    other_updates = []
    
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
                    "username": chat.get("username"),
                    "messages": []
                }
            
            channels[channel_id]["messages"].append(message[:60])
        else:
            # Other types of updates (DMs, group messages, etc.)
            if "message" in update:
                msg = update["message"]
                chat = msg["chat"]
                other_updates.append({
                    "type": chat.get("type"),
                    "title": chat.get("title") or f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip(),
                    "id": chat["id"]
                })
    
    if not channels:
        print("❌ No CHANNEL posts found!")
        print()
        
        if other_updates:
            print("⚠️  Found other updates (not channels):")
            for upd in other_updates[:5]:
                print(f"   - {upd['type']}: {upd['title']} (ID: {upd['id']})")
            print()
            print("💡 Make sure you:")
            print("   1. Created CHANNELS (not groups or DMs)")
            print("   2. Posted messages IN THE CHANNELS")
            print("   3. Bot is admin in the channels")
        else:
            print("🤔 The bot received updates but none from channels")
            print()
            print("Make sure:")
            print("   1. You created Telegram CHANNELS (not groups)")
            print("   2. Bot is ADMIN in those channels")
            print("   3. You posted a message IN the channels")
        
        exit(0)
    
    # Display results
    print("🎉 SUCCESS! Found your channels:")
    print("=" * 70)
    print()
    
    for channel_id, info in channels.items():
        print(f"📢 Channel: {info['title']}")
        print(f"   ID:       {channel_id}")
        print(f"   Type:     {info['type']}")
        if info.get('username'):
            print(f"   Username: @{info['username']}")
        print(f"   Messages: {len(info['messages'])}")
        if info['messages']:
            print(f"   Latest:   {info['messages'][-1]}")
        print()
    
    print("=" * 70)
    print("📋 COPY THIS TO YOUR .env FILE:")
    print("=" * 70)
    print()
    
    # Generate .env configuration
    public_found = False
    premium_found = False
    vip_found = False
    
    for channel_id, info in channels.items():
        title_lower = info['title'].lower()
        
        if "premium" in title_lower and not premium_found:
            print(f"TELEGRAM_PREMIUM_CHANNEL={channel_id}")
            premium_found = True
        elif "vip" in title_lower and not vip_found:
            print(f"TELEGRAM_VIP_CHANNEL={channel_id}")
            vip_found = True
        elif ("public" in title_lower or "deals" in title_lower or info.get('username')) and not public_found:
            if info.get('username'):
                print(f"TELEGRAM_PUBLIC_CHANNEL=@{info['username']}")
            else:
                print(f"TELEGRAM_PUBLIC_CHANNEL={channel_id}")
            public_found = True
        else:
            # Unknown channel
            print(f"# {info['title']}")
            if info.get('username'):
                print(f"# CHANNEL=@{info['username']}")
            else:
                print(f"# CHANNEL={channel_id}")
        print()
    
    print("=" * 70)
    print()
    print("✅ Done! Copy the IDs above to your .env file")
    print()
    
    if not premium_found:
        print("⚠️  Premium channel not found - did you name it 'Premium'?")
    if not vip_found:
        print("⚠️  VIP channel not found - did you name it 'VIP'?")
    if not public_found:
        print("⚠️  Public channel not found")
    
except requests.exceptions.RequestException as e:
    print(f"❌ Network Error: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
