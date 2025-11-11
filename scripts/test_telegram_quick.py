#!/usr/bin/env python3
"""
Quick test - Post a REAL listing to Telegram
Uses psycopg2 directly to avoid connection pool issues
"""
import sys
import os
import asyncio
import json
import psycopg2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from configs.settings import settings


async def post_test_listing():
    """Post a REAL listing from database"""
    print("=" * 60)
    print("🚀 Posting REAL Listing to Telegram")
    print("=" * 60)
    
    # Get listing data using psycopg2 directly
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="carscout_ai",
        user="carscout",
        password="password"
    )
    
    cur = conn.cursor()
    cur.execute("""
        SELECT id, url, parsed_data, site_ad_id
        FROM listings_raw
        WHERE is_active = true 
        AND parsed_data IS NOT NULL
        AND parsed_data->>'price' IS NOT NULL
        AND parsed_data->>'year' IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 1
    """)
    
    row = cur.fetchone()
    
    if not row:
        print("❌ No listings found")
        cur.close()
        conn.close()
        return
    
    listing_id, url, parsed_data, site_ad_id = row
    data = parsed_data
    
    print(f"\n📋 Selected: {data.get('brand')} {data.get('model')}")
    print(f"   Price: {data.get('price'):,} {data.get('currency', 'BGN')}")
    print(f"   Year: {data.get('year')}")
    
    cur.close()
    conn.close()
    
    # Format message
    brand = data.get('brand', 'Unknown')
    model = data.get('model', 'Model')
    year = data.get('year', 'N/A')
    price = int(data.get('price', 0))
    currency = data.get('currency', 'BGN')
    mileage = int(data.get('mileage_km', 0))
    fuel = data.get('fuel', 'N/A')
    gearbox = data.get('gearbox', 'N/A')
    
    message = f"""
🚗 <b>{brand} {model}</b> ({year})

💰 Price: <b>{price:,} {currency}</b>
⭐ Deal Score: <b>7.5/10</b> (TEST)

📊 Details:
• Year: {year}
• Mileage: {mileage:,} km
• Fuel: {fuel}
• Gearbox: {gearbox}

🔗 <a href="{url}">View Full Listing</a>

<i>🤖 Test post - Real listing from database (#22K+)</i>
"""
    
    # Keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 View", url=url)]
    ])
    
    # Post to Telegram
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    
    try:
        print("\n📱 Posting to Public channel...")
        msg = await bot.send_message(
            chat_id=settings.TELEGRAM_PUBLIC_CHANNEL,
            text=message,
            parse_mode="HTML",
            reply_markup=keyboard,
            disable_web_page_preview=False
        )
        print(f"✅ Posted! Message ID: {msg.message_id}")
        print(f"\n🎉 Check your Telegram channel!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(post_test_listing())
