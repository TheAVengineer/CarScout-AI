"""
Check bot privacy settings and clear old updates
Sometimes bots need privacy mode disabled to see channel posts
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

print("=" * 70)
print("🔍 Bot Privacy Mode Check & Update Clearer")
print("=" * 70)
print()

# Get bot info including privacy settings
print("Checking bot configuration...")
url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
response = requests.get(url)
data = response.json()

if data.get("ok"):
    bot_info = data["result"]
    print(f"✅ Bot: @{bot_info['username']}")
    
    # Check if bot can read all messages
    can_read = bot_info.get("can_read_all_group_messages", False)
    print(f"   Can read all messages: {can_read}")
    print()

print("=" * 70)
print("🔧 IMPORTANT: Bot Privacy Settings")
print("=" * 70)
print()
print("Go to @BotFather and check/change privacy mode:")
print()
print("1. Open Telegram and message @BotFather")
print("2. Send: /mybots")
print("3. Select: @carscout_bg_bot")
print("4. Click: Bot Settings")
print("5. Click: Group Privacy")
print("6. Choose: DISABLE (Turn OFF privacy mode)")
print()
print("This allows the bot to see ALL messages in channels/groups.")
print()
print("⚠️  Privacy mode DISABLED is REQUIRED for channel posts!")
print()
print("=" * 70)
print()

# Now let's clear old updates and get fresh ones
print("Clearing old updates...")
url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset=-1"
response = requests.get(url)
data = response.json()

if data.get("ok") and data.get("result"):
    # Get last update ID and skip past it
    updates = data["result"]
    if updates:
        last_id = max(u["update_id"] for u in updates)
        # Acknowledge all old updates
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_id + 1}")
        print(f"✅ Cleared {len(updates)} old updates")
    else:
        print("✅ No old updates to clear")
else:
    print("✅ No old updates")

print()
print("=" * 70)
print("📝 ACTION REQUIRED:")
print("=" * 70)
print()
print("1. Go to @BotFather → /mybots → @carscout_bg_bot")
print("2. Bot Settings → Group Privacy → DISABLE")
print("3. Go to your channels and post a NEW message: 'Test 2'")
print("4. Wait 10 seconds")
print("5. Run this command:")
print()
print("   python scripts/get_channel_ids_simple.py")
print()
print("=" * 70)
