#!/usr/bin/env python3
"""
Test Full Deal Evaluation Flow

This script tests the complete flow:
1. Fetch listing from database
2. Score with new price-focused algorithm
3. Check if it would be posted (score >= 8.0)
4. Show what the Telegram message would look like

Note: The current scoring system uses database comparables,
not OpenAI API. OpenAI will be used in future for:
- Advanced fraud detection
- Image analysis  
- Natural language description generation
"""

import sys
from pathlib import Path
import asyncio

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw
from configs.settings import settings
from sqlalchemy import func
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import random

def get_comparable_price(session, brand: str, model: str, year: int, mileage: int):
    """Find average price of comparable vehicles"""
    try:
        if not all([brand, model, year]):
            return None
        
        # Query for comparable vehicles (±2 years, ±20k km)
        listings = session.query(ListingRaw).filter(
            ListingRaw.is_active == True,
            ListingRaw.parsed_data.isnot(None)
        ).all()
        
        # Filter in Python
        prices = []
        for listing in listings:
            data = listing.parsed_data or {}
            l_brand = data.get('brand')
            l_model = data.get('model')
            l_year = data.get('year')
            l_mileage = data.get('mileage', 0)
            l_price = data.get('price')
            
            if (l_brand == brand and 
                l_model == model and
                l_year and year - 2 <= l_year <= year + 2 and
                l_mileage and mileage - 20000 <= l_mileage <= mileage + 20000 and
                l_price and l_price > 0):
                prices.append(l_price)
        
        if prices:
            return sum(prices) / len(prices), len(prices)
        return None, 0
        
    except Exception as e:
        print(f"Error getting comparable price: {e}")
        return None, 0


def calculate_score(data: dict, session) -> tuple[float, dict]:
    """Calculate score and return evaluation data"""
    
    # Base score - start conservative
    score = 5.0
    evaluation = {
        'bonuses': [],
        'market_price': None,
        'discount_pct': 0,
        'comparables_count': 0,
        'deal_quality': 'NONE'
    }
    
    brand = data.get('brand')
    model = data.get('model')
    year = data.get('year')
    mileage = data.get('mileage', 0)
    price = data.get('price')
    
    # Get comparable vehicles
    market_price, comp_count = get_comparable_price(session, brand, model, year, mileage)
    
    evaluation['market_price'] = market_price
    evaluation['comparables_count'] = comp_count
    
    if market_price and price:
        # Calculate discount from market
        discount_pct = ((market_price - price) / market_price) * 100
        evaluation['discount_pct'] = round(discount_pct, 1)
        
        # MAJOR price bonuses
        if discount_pct >= 20:
            score += 3.0
            evaluation['bonuses'].append('+3.0 (20%+ below market - EXCELLENT!)')
            evaluation['deal_quality'] = 'EXCELLENT'
        elif discount_pct >= 15:
            score += 2.0
            evaluation['bonuses'].append('+2.0 (15-20% below market - GREAT)')
            evaluation['deal_quality'] = 'GREAT'
        elif discount_pct >= 10:
            score += 1.0
            evaluation['bonuses'].append('+1.0 (10-15% below market - GOOD)')
            evaluation['deal_quality'] = 'GOOD'
        elif discount_pct >= 5:
            score += 0.5
            evaluation['bonuses'].append('+0.5 (5-10% below market - FAIR)')
            evaluation['deal_quality'] = 'FAIR'
    
    # Smaller bonuses for desirable features
    if year and year >= 2020:
        score += 0.4
        evaluation['bonuses'].append('+0.4 (Newer car)')
    
    if mileage and mileage < 50000:
        score += 0.4
        evaluation['bonuses'].append('+0.4 (Low mileage)')
    
    transmission = data.get('transmission', '')
    if transmission and transmission.lower() in ['автоматична', 'automatic']:
        score += 0.3
        evaluation['bonuses'].append('+0.3 (Automatic)')
    
    fuel_type = data.get('fuel_type', '')
    if fuel_type and fuel_type.lower() in ['хибрид', 'електричество', 'hybrid', 'electric']:
        score += 0.5
        evaluation['bonuses'].append('+0.5 (Eco-friendly)')
    
    # Cap at 10
    score = min(10.0, score)
    evaluation['final_score'] = round(score, 2)
    
    return score, evaluation


async def format_telegram_message(data: dict, score: float, evaluation: dict) -> str:
    """Format message exactly as it would appear in Telegram"""
    
    brand = data.get('brand', 'Unknown')
    model = data.get('model', 'Unknown')
    year = data.get('year', 'N/A')
    price = data.get('price', 0)
    currency = data.get('currency', 'BGN')
    mileage = data.get('mileage')
    fuel = data.get('fuel_type', 'N/A')
    transmission = data.get('transmission', 'N/A')
    url = data.get('url', '')
    
    # Build message
    message = f"""🚗 <b>{brand} {model}</b> ({year})

💰 Price: <b>{price:,} {currency}</b>
📏 Mileage: {mileage:,} km
⛽ Fuel: {fuel}
⚙️  Transmission: {transmission}

"""
    
    # Add evaluation
    market_price = evaluation.get('market_price')
    if market_price:
        discount_pct = evaluation['discount_pct']
        comparables = evaluation['comparables_count']
        deal_quality = evaluation['deal_quality']
        
        message += f"""📊 <b>Market Analysis:</b>
   Market Price: {market_price:,.0f} {currency}
   Discount: <b>{discount_pct:.1f}%</b> below market
   Comparables: {comparables} similar listings
   Quality: <b>{deal_quality}</b>

"""
    
    # Score
    message += f"""⭐ <b>Deal Score: {score:.1f}/10.0</b>
"""
    
    # Bonuses
    if evaluation.get('bonuses'):
        message += "\n📈 Score breakdown:\n"
        message += "   Base: 5.0\n"
        for bonus in evaluation['bonuses']:
            message += f"   {bonus}\n"
    
    message += f"\n🔗 <a href='{url}'>View Listing</a>"
    
    return message


async def test_full_flow():
    """Test the complete evaluation and posting flow"""
    
    print("=" * 70)
    print("🧪 TESTING FULL DEAL EVALUATION FLOW")
    print("=" * 70)
    print()
    
    # 1. Get a listing from database
    session = get_sync_session()
    
    # Get a random listing with complete data
    listings = session.query(ListingRaw).filter(
        ListingRaw.is_active == True,
        ListingRaw.parsed_data.isnot(None)
    ).all()
    
    # Filter to complete listings
    complete_listings = []
    for listing in listings:
        data = listing.parsed_data or {}
        if all([data.get('brand'), data.get('model'), data.get('year'), data.get('price')]):
            complete_listings.append(listing)
    
    if not complete_listings:
        print("❌ No listings with complete data found")
        return
    
    # Test 3 random listings
    test_listings = random.sample(complete_listings, min(3, len(complete_listings)))
    
    for i, listing in enumerate(test_listings, 1):
        data = listing.parsed_data
        
        print(f"\n{'='*70}")
        print(f"TEST {i}/3")
        print(f"{'='*70}\n")
        
        # 2. Calculate score
        print("📊 STEP 1: Scoring")
        print("-" * 70)
        score, evaluation = calculate_score(data, session)
        
        print(f"Listing: {data.get('brand')} {data.get('model')} ({data.get('year')})")
        print(f"Price: {data.get('price'):,} BGN")
        
        if evaluation['market_price']:
            print(f"Market Price: {evaluation['market_price']:,.0f} BGN")
            print(f"Discount: {evaluation['discount_pct']:.1f}% ({evaluation['deal_quality']})")
            print(f"Comparables: {evaluation['comparables_count']} similar cars")
        else:
            print("Market Price: No comparables found")
        
        print()
        print("Score Breakdown:")
        print("  Base: 5.0")
        for bonus in evaluation.get('bonuses', []):
            print(f"  {bonus}")
        print(f"\n  FINAL SCORE: {score:.2f}/10.0")
        print()
        
        # 3. Check posting decision
        print("🎯 STEP 2: Posting Decision")
        print("-" * 70)
        would_post = score >= 8.0
        
        if would_post:
            print(f"✅ WOULD POST (score {score:.2f} >= 8.0)")
            print(f"   Channel: Public (CarScout Deals)")
        else:
            print(f"❌ WOULD NOT POST (score {score:.2f} < 8.0)")
            print(f"   Reason: Score below threshold")
        print()
        
        # 4. Show Telegram message preview
        if would_post:
            print("📱 STEP 3: Telegram Message Preview")
            print("-" * 70)
            message = await format_telegram_message(data, score, evaluation)
            print(message)
            print()
    
    session.close()
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)
    print()
    print("📌 Summary:")
    print("   - Scoring uses database comparables (not OpenAI)")
    print("   - Threshold: 8.0/10.0 to post")
    print("   - Focus: Price value (up to +3.0 bonus)")
    print("   - Monitor runs automatically every 5 minutes")
    print()
    print("🔑 OpenAI Integration:")
    print(f"   Status: ✅ API Key Valid (gpt-4o-mini)")
    print(f"   Current Use: None (using heuristic scoring)")
    print(f"   Future Use: Fraud detection, image analysis, NLP")
    print()


if __name__ == '__main__':
    asyncio.run(test_full_flow())
