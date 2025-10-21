"""
Diagnostic: Check bot info and help troubleshoot channel setup
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

print("=" * 70)
print("🔍 Telegram Bot Diagnostic")
print("=" * 70)
print()

# Step 1: Get bot info
print("Step 1: Checking bot info...")
url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
response = requests.get(url)
data = response.json()

if data.get("ok"):
    bot_info = data["result"]
    print(f"✅ Bot is working!")
    print(f"   Username: @{bot_info['username']}")
    print(f"   Name: {bot_info['first_name']}")
    print(f"   ID: {bot_info['id']}")
else:
    print(f"❌ Bot error: {data}")
    exit(1)

print()

# Step 2: Check updates
print("Step 2: Checking recent updates...")
url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
response = requests.get(url)
data = response.json()

if not data.get("ok"):
    print(f"❌ Error: {data}")
    exit(1)

updates = data.get("result", [])
print(f"   Found {len(updates)} updates total")
print()

# Analyze updates
has_private_messages = False
has_group_messages = False
has_channel_posts = False
channel_count = 0

for update in updates:
    if "message" in update:
        chat_type = update["message"]["chat"]["type"]
        if chat_type == "private":
            has_private_messages = True
        elif chat_type in ["group", "supergroup"]:
            has_group_messages = True
    
    if "channel_post" in update:
        has_channel_posts = True
        channel_count += 1

print("=" * 70)
print("📊 Update Analysis:")
print("=" * 70)
print()

if has_private_messages:
    print("✅ Found private messages (DMs to bot)")
else:
    print("⚪ No private messages")

if has_group_messages:
    print("✅ Found group messages")
else:
    print("⚪ No group messages")

if has_channel_posts:
    print(f"✅ Found {channel_count} channel posts!")
else:
    print("❌ No channel posts found")

print()
print("=" * 70)

if not has_channel_posts:
    print("❌ PROBLEM: Bot is not receiving channel posts")
    print("=" * 70)
    print()
    print("🔧 TROUBLESHOOTING STEPS:")
    print()
    print("1. ✅ Make sure you created CHANNELS (not groups)")
    print("   → Telegram → New CHANNEL (not New Group)")
    print()
    print("2. ✅ Add bot as ADMINISTRATOR to each channel:")
    print("   → Open channel → Settings → Administrators")
    print("   → Add Administrator → Search: @carscout_bg_bot")
    print("   → Enable: 'Post Messages'")
    print("   → Click Save")
    print()
    print("3. ✅ POST a message IN THE CHANNEL:")
    print("   → Open the channel (as admin)")
    print("   → Type: 'Test from admin'")
    print("   → Send")
    print()
    print("4. ✅ Wait 10 seconds, then run this script again")
    print()
    print("=" * 70)
    print()
    print("💡 COMMON MISTAKES:")
    print()
    print("❌ Creating a GROUP instead of a CHANNEL")
    print("   → Groups have members who can chat")
    print("   → Channels have subscribers who can only view")
    print()
    print("❌ Adding bot as MEMBER instead of ADMIN")
    print("   → Bot must be Administrator to receive posts")
    print()
    print("❌ Not giving 'Post Messages' permission")
    print("   → Bot needs this permission")
    print()
    print("❌ Sending message TO the bot instead of IN the channel")
    print("   → Post in the channel itself, not bot's DM")
    print()
else:
    print("🎉 SUCCESS! Channel posts detected!")
    print("=" * 70)
    print()
    print("Run this to get your channel IDs:")
    print()
    print("   python scripts/get_channel_ids_simple.py")
    print()

print("=" * 70)
print()

# Show detailed update types
if updates:
    print("📄 Detailed update breakdown:")
    print()
    
    update_types = {}
    for update in updates:
        if "message" in update:
            chat_type = update["message"]["chat"]["type"]
            key = f"message ({chat_type})"
        elif "channel_post" in update:
            key = "channel_post"
        elif "edited_message" in update:
            key = "edited_message"
        elif "edited_channel_post" in update:
            key = "edited_channel_post"
        else:
            key = "other"
        
        update_types[key] = update_types.get(key, 0) + 1
    
    for update_type, count in update_types.items():
        print(f"   {update_type}: {count}")
    
    print()
