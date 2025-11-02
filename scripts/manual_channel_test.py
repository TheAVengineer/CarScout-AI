"""
Alternative method: Manually test posting to channel with channel ID or username
This will help us figure out what's going on
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

print("=" * 70)
print("🧪 Manual Channel Test")
print("=" * 70)
print()
print("This will help us figure out why the bot isn't seeing your posts.")
print()
print("We'll try a different approach:")
print("=" * 70)
print()

# Method 1: Try with username if it's a public channel
print("METHOD 1: If you have a PUBLIC channel with username")
print()
channel_username = input("Enter channel username (e.g., @CarScoutDeals) or leave empty to skip: ").strip()

if channel_username:
    if not channel_username.startswith("@"):
        channel_username = "@" + channel_username
    
    print()
    print(f"Testing posting to {channel_username}...")
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": channel_username,
        "text": "🤖 Test post from bot - if you see this, the bot can post!"
    }
    
    response = requests.post(url, json=payload)
    data = response.json()
    
    if data.get("ok"):
        result = data["result"]
        chat = result["chat"]
        
        print()
        print("=" * 70)
        print("✅ SUCCESS! Bot can post to this channel!")
        print("=" * 70)
        print()
        print(f"📢 Channel: {chat.get('title', 'Unknown')}")
        print(f"   ID: {chat['id']}")
        print(f"   Type: {chat.get('type')}")
        if chat.get('username'):
            print(f"   Username: @{chat['username']}")
        print()
        print("💾 Add to .env:")
        if chat.get('username'):
            print(f"TELEGRAM_PUBLIC_CHANNEL=@{chat['username']}")
        else:
            print(f"TELEGRAM_PUBLIC_CHANNEL={chat['id']}")
        print()
    else:
        print()
        print(f"❌ Error: {data.get('description', 'Unknown error')}")
        print()
        
        error_desc = data.get('description', '')
        if 'bot is not a member' in error_desc.lower():
            print("💡 Fix: Add bot as admin to the channel")
        elif 'chat not found' in error_desc.lower():
            print("💡 Fix: Check the channel username is correct")
        elif 'have no rights' in error_desc.lower():
            print("💡 Fix: Give bot 'Post Messages' permission")
    
    print()

# Method 2: Try with channel ID if it's private
print("=" * 70)
print("METHOD 2: If you have a PRIVATE channel")
print("=" * 70)
print()
print("For private channels, we need the numeric ID.")
print()
print("Try this:")
print("1. Add me (your personal account) to the channel")
print("2. Forward any message from the channel to @userinfobot")
print("3. It will show you the channel ID")
print()
channel_id = input("Enter channel ID (e.g., -1001234567890) or leave empty to skip: ").strip()

if channel_id:
    print()
    print(f"Testing posting to {channel_id}...")
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": "🤖 Test post from bot - if you see this, the bot can post!"
    }
    
    response = requests.post(url, json=payload)
    data = response.json()
    
    if data.get("ok"):
        result = data["result"]
        chat = result["chat"]
        
        print()
        print("=" * 70)
        print("✅ SUCCESS! Bot can post to this channel!")
        print("=" * 70)
        print()
        print(f"📢 Channel: {chat.get('title', 'Unknown')}")
        print(f"   ID: {chat['id']}")
        print(f"   Type: {chat.get('type')}")
        print()
        print("💾 Add to .env:")
        
        title_lower = chat.get('title', '').lower()
        if 'premium' in title_lower:
            print(f"TELEGRAM_PREMIUM_CHANNEL={chat['id']}")
        elif 'vip' in title_lower:
            print(f"TELEGRAM_VIP_CHANNEL={chat['id']}")
        else:
            print(f"TELEGRAM_CHANNEL={chat['id']}")
        print()
    else:
        print()
        print(f"❌ Error: {data.get('description', 'Unknown error')}")
        print()
        
        error_desc = data.get('description', '')
        if 'bot is not a member' in error_desc.lower():
            print("💡 Fix: Add bot as admin to the channel")
        elif 'chat not found' in error_desc.lower():
            print("💡 Fix: Check the channel ID is correct")
        elif 'have no rights' in error_desc.lower():
            print("💡 Fix: Give bot 'Post Messages' permission")
    
    print()

print("=" * 70)
print("🔍 ALTERNATIVE METHOD: Use @userinfobot")
print("=" * 70)
print()
print("If the above didn't work, try this reliable method:")
print()
print("1. Add @userinfobot to your channel (as member or admin)")
print("2. Forward any message from the channel to @userinfobot")
print("3. It will reply with the channel ID")
print("4. Use that ID in your .env file")
print()
print("This works 100% of the time for getting channel IDs!")
print()
print("=" * 70)
