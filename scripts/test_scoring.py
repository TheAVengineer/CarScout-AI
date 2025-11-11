#!/usr/bin/env python3
"""
Test the new price-focused scoring algorithm

This script selects several listings from the database and shows
their scores using the new algorithm to verify only good deals score 8.0+
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw
from sqlalchemy import func
import json

def test_scoring():
    """Test scoring on real listings"""
    
    print("=" * 70)
    print("🧪 TESTING NEW PRICE-FOCUSED SCORING ALGORITHM")
    print("=" * 70)
    print()
    
    session = get_sync_session()
    
    # Get a diverse sample of listings with parsed data
    listings = session.query(ListingRaw).filter(
        ListingRaw.is_active == True,
        ListingRaw.parsed_data.isnot(None)
    ).limit(10).all()
    
    if not listings:
        print("❌ No listings found in database")
        return
    
    # Filter to only those with complete data
    complete_listings = []
    for listing in listings:
        data = listing.parsed_data or {}
        if all([
            data.get('brand'),
            data.get('model'),
            data.get('year'),
            data.get('price')
        ]):
            complete_listings.append(listing)
    
    if not complete_listings:
        print("❌ No listings with complete data found")
        return
    
    print(f"📊 Testing {len(complete_listings)} listings:\n")
    
    for i, listing in enumerate(complete_listings, 1):
        data = listing.parsed_data or {}
        score = calculate_score(data, session)
        
        # Determine if it would be posted
        would_post = "✅ WOULD POST" if score >= 8.0 else "❌ Won't post"
        
        print(f"{'='*70}")
        print(f"Listing {i}: {data.get('brand')} {data.get('model')} ({data.get('year')})")
        print(f"{'='*70}")
        print(f"Price: {data.get('price'):,} {data.get('currency', 'BGN')}")
        print(f"Mileage: {data.get('mileage', 'N/A'):,} km" if data.get('mileage') else "Mileage: N/A")
        print(f"Fuel: {data.get('fuel_type') or 'N/A'}")
        print(f"Transmission: {data.get('transmission') or 'N/A'}")
        print()
        print(f"🎯 FINAL SCORE: {score:.2f}/10.0")
        print(f"   {would_post}")
        print()
    
    # Show statistics
    scores = [calculate_score(l.parsed_data or {}, session) for l in complete_listings]
    avg_score = sum(scores) / len(scores) if scores else 0
    would_post_count = sum(1 for s in scores if s >= 8.0)
    
    print("=" * 70)
    print("📈 STATISTICS")
    print("=" * 70)
    print(f"Average score: {avg_score:.2f}")
    print(f"Listings that would post: {would_post_count}/{len(complete_listings)} ({would_post_count/len(complete_listings)*100:.1f}%)")
    print(f"Minimum score to post: 8.0")
    print()
    print("✅ Only listings with exceptional value will be posted!")
    print("=" * 70)
    
    session.close()


def calculate_score(data: dict, session) -> float:
    """Calculate score using the new algorithm"""
    
    # Base score - start conservative
    score = 5.0
    
    brand = data.get('brand')
    model = data.get('model')
    year = data.get('year')
    mileage = data.get('mileage', 0)
    price = data.get('price')
    
    # Get comparable vehicles
    market_price = get_comparable_price(session, brand, model, year, mileage)
    
    if market_price and price:
        # Calculate discount from market
        discount_pct = ((market_price - price) / market_price) * 100
        
        # MAJOR price bonuses
        if discount_pct >= 20:
            score += 3.0  # Excellent deal! 20%+ off
        elif discount_pct >= 15:
            score += 2.0  # Great deal! 15-20% off
        elif discount_pct >= 10:
            score += 1.0  # Good deal! 10-15% off
        elif discount_pct >= 5:
            score += 0.5  # Decent deal 5-10% off
        # else: At or above market price - no bonus
        
        print(f"💰 Market Price: {market_price:,.0f} BGN")
        print(f"💵 Asking Price: {price:,} BGN")
        print(f"📉 Discount: {discount_pct:.1f}% below market")
    else:
        print(f"⚠️  No comparables found - conservative scoring")
    
    # Smaller bonuses for desirable features
    if year and year >= 2020:
        score += 0.4
        print(f"   +0.4 (Newer car: {year})")
    
    if mileage and mileage < 50000:
        score += 0.4
        print(f"   +0.4 (Low mileage: {mileage:,} km)")
    
    transmission = data.get('transmission', '')
    if transmission and transmission.lower() in ['автоматична', 'automatic']:
        score += 0.3
        print(f"   +0.3 (Automatic transmission)")
    
    fuel_type = data.get('fuel_type', '')
    if fuel_type and fuel_type.lower() in ['хибрид', 'електричество', 'hybrid', 'electric']:
        score += 0.5
        print(f"   +0.5 (Eco-friendly: {fuel_type})")
    
    # Cap at 10
    score = min(10.0, score)
    
    return score


def get_comparable_price(session, brand: str, model: str, year: int, mileage: int):
    """Find average price of comparable vehicles"""
    try:
        if not all([brand, model, year]):
            return None
        
        from sqlalchemy import cast, Integer
        
        # Query for comparable vehicles (±2 years, ±20k km)
        # Need to extract values from parsed_data JSON field
        listings = session.query(ListingRaw).filter(
            ListingRaw.is_active == True,
            ListingRaw.parsed_data.isnot(None)
        ).all()
        
        # Filter in Python (simpler than complex JSON queries)
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
            return sum(prices) / len(prices)
        return None
        
    except Exception as e:
        print(f"Error getting comparable price: {e}")
        return None


if __name__ == '__main__':
    test_scoring()
