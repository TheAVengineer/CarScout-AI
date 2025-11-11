"""
Test posting a REAL listing from database to Telegram
Uses actual data to verify integration and tune scoring
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from configs.settings import settings
from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw
from sqlalchemy import func


async def post_test_listing():
    """Post a REAL car listing from database to Telegram"""
    print("=" * 60)
    print("🚀 Posting REAL Listing to Telegram Channels")
    print("=" * 60)
    
    # Get a random good listing from database
    session = get_sync_session()
    
    listing = session.query(ListingRaw).filter(
        ListingRaw.is_active == True,
        ListingRaw.parsed_data.isnot(None)
    ).order_by(func.random()).limit(10).all()
    
    # Find one with good data
    good_listing = None
    for l in listing:
        data = l.parsed_data or {}
        if data.get('price') and data.get('year') and int(data.get('year', 0)) >= 2010:
            good_listing = l
            break
    
    if not good_listing:
        print("❌ No suitable listings found in database")
        session.close()
        return
    
    listing = good_listing
    data = listing.parsed_data or {}
    
    print(f"\n📋 Selected listing from database:")
    print(f"   Brand/Model: {data.get('brand')} {data.get('model')}")
    print(f"   Price: {data.get('price'):,} {data.get('currency', 'BGN')}")
    print(f"   Year: {data.get('year')}")
    print(f"   Mileage: {data.get('mileage_km', 0):,} km")
    print(f"   URL: {listing.url}")
    
    session.close()
    
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    
    # Format message with REAL data
    brand = data.get('brand', 'Unknown')
    model = data.get('model', 'Model')
    year = data.get('year', 'N/A')
    price = data.get('price', 0)
    currency = data.get('currency', 'BGN')
    mileage = data.get('mileage_km', 0)
    fuel = data.get('fuel', 'N/A')
    gearbox = data.get('gearbox', 'N/A')
    body = data.get('body', 'N/A')
    region = data.get('region', 'Bulgaria')
    
    message = f"""
🚗 <b>{brand} {model}</b> ({year})

💰 Price: <b>{price:,.0f} {currency}</b>
⭐ Deal Score: <b>7.5/10</b> (TEST)

📊 Details:
• Year: {year}
• Mileage: {mileage:,.0f} km
• Fuel: {fuel}
• Gearbox: {gearbox}
• Body: {body}

📍 Location: {region}
🔗 <a href="{listing.url}">View Full Listing</a>

<i>🤖 Test post - Real listing from database</i>
"""

    # Create inline keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔗 View Listing", url=listing.url),
            InlineKeyboardButton(text="❤️ Save", callback_data=f"save_{listing.id}")
        ],
        [
            InlineKeyboardButton(text="🔍 Similar", callback_data=f"similar_{listing.id}"),
            InlineKeyboardButton(text="📊 History", callback_data=f"history_{listing.id}")
        ]
    ])
    
    try:
        # Try with photo if available
        images = data.get('images', [])
        if images and len(images) > 0:
            first_image = images[0] if isinstance(images, list) else images
            print(f"\n📸 Sending with photo...")
            
            # Post to Public channel
            print("\n📱 Posting to Public channel...")
            msg1 = await bot.send_photo(
                chat_id=settings.TELEGRAM_PUBLIC_CHANNEL,
                photo=first_image,
                caption=message,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            print(f"  ✅ Posted! Message ID: {msg1.message_id}")
        else:
            print(f"\n📝 Sending as text (no images)...")
            
            # Post to Public channel
            print("\n📱 Posting to Public channel...")
            msg1 = await bot.send_message(
                chat_id=settings.TELEGRAM_PUBLIC_CHANNEL,
                text=message,
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=False
            )
            print(f"  ✅ Posted! Message ID: {msg1.message_id}")
        
        # Post to Premium channel
        print("\n📱 Posting to Premium channel...")
        msg2 = await bot.send_message(
            chat_id=settings.TELEGRAM_PREMIUM_CHANNEL,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        print(f"  ✅ Posted! Message ID: {msg2.message_id}")
        
        # Post to VIP channel
        print("\n📱 Posting to VIP channel...")
        msg3 = await bot.send_message(
            chat_id=settings.TELEGRAM_VIP_CHANNEL,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        print(f"  ✅ Posted! Message ID: {msg3.message_id}")
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Test listing posted to all channels!")
        print("=" * 60)
        print("\n📱 Check your Telegram channels:")
        print(f"   • Public: @CarScoutBG")
        print(f"   • Premium: {settings.TELEGRAM_PREMIUM_CHANNEL}")
        print(f"   • VIP: {settings.TELEGRAM_VIP_CHANNEL}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(post_test_listing())
