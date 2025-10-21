"""
Test posting to configured channels
"""
import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PUBLIC_CHANNEL = os.getenv("TELEGRAM_PUBLIC_CHANNEL")
PREMIUM_CHANNEL = os.getenv("TELEGRAM_PREMIUM_CHANNEL")
VIP_CHANNEL = os.getenv("TELEGRAM_VIP_CHANNEL")

print("=" * 70)
print("📺 Testing Channel Posting")
print("=" * 70)
print()
print(f"Bot Token: {BOT_TOKEN[:20]}...")
print(f"Public Channel: {PUBLIC_CHANNEL}")
print(f"Premium Channel: {PREMIUM_CHANNEL}")
print(f"VIP Channel: {VIP_CHANNEL}")
print()
print("=" * 70)
print()


async def test_channel(bot: Bot, channel_id: str, channel_name: str):
    """Test posting to a channel"""
    try:
        message = await bot.send_message(
            chat_id=channel_id,
            text=f"🤖 Test post to {channel_name}\n\n✅ Bot is working correctly!",
            parse_mode="HTML"
        )
        
        print(f"✅ {channel_name}")
        print(f"   Channel ID: {channel_id}")
        print(f"   Message ID: {message.message_id}")
        print(f"   Posted successfully!")
        print()
        return True
        
    except Exception as e:
        print(f"❌ {channel_name}")
        print(f"   Channel ID: {channel_id}")
        print(f"   Error: {e}")
        print()
        
        error_str = str(e).lower()
        if "bot is not a member" in error_str or "chat not found" in error_str:
            print(f"   💡 Fix: Add @carscout_bg_bot as admin to this channel")
        elif "not enough rights" in error_str or "no rights" in error_str:
            print(f"   💡 Fix: Give bot 'Post Messages' permission")
        
        print()
        return False


async def main():
    """Test all channels"""
    bot = Bot(token=BOT_TOKEN)
    
    results = []
    
    # Test Public Channel
    if PUBLIC_CHANNEL:
        print("Testing Public Channel...")
        success = await test_channel(bot, PUBLIC_CHANNEL, "Public Channel (FREE)")
        results.append(("Public", success))
    else:
        print("⚠️  Public channel not configured")
        results.append(("Public", False))
    
    # Test Premium Channel
    if PREMIUM_CHANNEL and PREMIUM_CHANNEL != "-1001234567890":
        print("Testing Premium Channel...")
        success = await test_channel(bot, PREMIUM_CHANNEL, "Premium Channel (€14.99/mo)")
        results.append(("Premium", success))
    else:
        print("⚠️  Premium channel not configured")
        results.append(("Premium", False))
    
    # Test VIP Channel
    if VIP_CHANNEL and VIP_CHANNEL != "-1009876543210":
        print("Testing VIP Channel...")
        success = await test_channel(bot, VIP_CHANNEL, "VIP Channel (€29.99/mo)")
        results.append(("VIP", success))
    else:
        print("⚠️  VIP channel not configured (you'll create it later)")
        results.append(("VIP", None))
    
    await bot.session.close()
    
    print("=" * 70)
    print("📊 RESULTS:")
    print("=" * 70)
    print()
    
    for channel_name, success in results:
        if success is True:
            print(f"✅ {channel_name} Channel: Working!")
        elif success is False:
            print(f"❌ {channel_name} Channel: Failed")
        else:
            print(f"⚪ {channel_name} Channel: Not configured yet")
    
    print()
    
    successful = sum(1 for _, s in results if s is True)
    total = sum(1 for _, s in results if s is not None)
    
    if successful == total and total > 0:
        print("🎉 All configured channels are working!")
        print()
        print("Next steps:")
        print("1. Create VIP channel when ready")
        print("2. Configure OpenAI API key for AI analysis")
        print("3. Configure Stripe for payments")
        print("4. Start the services!")
    elif successful > 0:
        print(f"⚠️  {successful}/{total} channels working")
        print()
        print("Fix the failed channels before proceeding.")
    else:
        print("❌ No channels working")
        print()
        print("Make sure bot is admin in all channels with 'Post Messages' permission")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
