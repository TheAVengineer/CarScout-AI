#!/usr/bin/env python3
"""
Test the improved scoring system with realistic examples
"""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw
from sqlalchemy import func
from datetime import datetime

def get_comparable_price(session, brand, model, year, mileage):
    """Get average price of comparable vehicles"""
    query = session.query(func.avg(ListingRaw.parsed_data['price'].astext.cast(float))).filter(
        ListingRaw.parsed_data['brand'].astext == brand,
        ListingRaw.parsed_data['model'].astext == model,
        ListingRaw.parsed_data['year'].astext.cast(int).between(year - 2, year + 2),
        ListingRaw.parsed_data['mileage'].astext.cast(int).between(mileage - 20000, mileage + 20000),
        ListingRaw.is_active == True
    )
    avg_price = query.scalar()
    return float(avg_price) if avg_price else None

def count_comparables(session, brand, model, year, mileage):
    """Count comparable vehicles"""
    query = session.query(func.count()).filter(
        ListingRaw.parsed_data['brand'].astext == brand,
        ListingRaw.parsed_data['model'].astext == model,
        ListingRaw.parsed_data['year'].astext.cast(int).between(year - 2, year + 2),
        ListingRaw.parsed_data['mileage'].astext.cast(int).between(mileage - 20000, mileage + 20000),
        ListingRaw.is_active == True
    )
    return query.scalar()

def calculate_score(asking_price, market_price, comparables_count, year, mileage, is_automatic, is_eco):
    """Calculate score using new algorithm"""
    
    # Base score
    score = 4.0
    
    if market_price and comparables_count >= 5:
        # Calculate real discount
        discount_pct = ((market_price - asking_price) / market_price) * 100
        
        # Confidence factor
        if comparables_count >= 20:
            confidence = 1.0
        elif comparables_count >= 10:
            confidence = 0.8
        else:
            confidence = 0.6
        
        # Price scoring
        if discount_pct >= 25:
            score += 3.5 * confidence
            quality = "EXCEPTIONAL"
        elif discount_pct >= 20:
            score += 3.0 * confidence
            quality = "EXCELLENT"
        elif discount_pct >= 15:
            score += 2.0 * confidence
            quality = "GREAT"
        elif discount_pct >= 10:
            score += 1.0 * confidence
            quality = "GOOD"
        elif discount_pct >= 5:
            score += 0.5 * confidence
            quality = "FAIR"
        elif discount_pct >= 0:
            score += 0.0
            quality = "MARKET_PRICE"
        else:
            score -= 1.0
            quality = "OVERPRICED"
    else:
        discount_pct = 0
        confidence = 0
        quality = "UNKNOWN"
        score = 3.0
    
    # Feature bonuses
    if year >= 2020:
        score += 0.3
    if mileage < 50000:
        score += 0.3
    if is_automatic:
        score += 0.2
    if is_eco:
        score += 0.4
    
    score = min(10.0, max(1.0, score))
    
    return score, discount_pct, quality, confidence


def main():
    session = get_sync_session()
    
    print("🧪 Testing Improved Scoring System")
    print("=" * 80)
    print()
    
    # Test scenarios
    scenarios = [
        {
            "name": "Fake Discount Scam",
            "brand": "BMW",
            "model": "3 Series",
            "year": 2018,
            "mileage": 120000,
            "asking_price": 19000,
            "seller_claimed_original": 25000,  # FAKE!
            "is_automatic": True,
            "is_eco": False,
        },
        {
            "name": "Real Deal - Exceptional",
            "brand": "Mercedes-Benz",
            "model": "A-Class",
            "year": 2019,
            "mileage": 80000,
            "asking_price": 18000,
            "is_automatic": True,
            "is_eco": False,
        },
        {
            "name": "Market Price (Not a Deal)",
            "brand": "VW",
            "model": "Golf",
            "year": 2017,
            "mileage": 100000,
            "asking_price": 12000,
            "is_automatic": False,
            "is_eco": False,
        },
    ]
    
    for scenario in scenarios:
        print(f"📋 Scenario: {scenario['name']}")
        print("-" * 80)
        
        # Get market data
        market_price = get_comparable_price(
            session, 
            scenario['brand'], 
            scenario['model'], 
            scenario['year'], 
            scenario['mileage']
        )
        
        comparables_count = count_comparables(
            session,
            scenario['brand'],
            scenario['model'],
            scenario['year'],
            scenario['mileage']
        )
        
        # Calculate score
        score, discount_pct, quality, confidence = calculate_score(
            scenario['asking_price'],
            market_price,
            comparables_count,
            scenario['year'],
            scenario['mileage'],
            scenario.get('is_automatic', False),
            scenario.get('is_eco', False)
        )
        
        # Display results
        print(f"Car: {scenario['brand']} {scenario['model']} {scenario['year']}")
        print(f"Mileage: {scenario['mileage']:,} km")
        print(f"Asking Price: €{scenario['asking_price']:,}")
        
        if 'seller_claimed_original' in scenario:
            fake_discount = ((scenario['seller_claimed_original'] - scenario['asking_price']) / scenario['seller_claimed_original']) * 100
            print(f"❌ Seller Claims: €{scenario['seller_claimed_original']:,} → €{scenario['asking_price']:,} ({fake_discount:.1f}% OFF)")
        
        print()
        print(f"✅ REAL Market Price: €{market_price:,.0f}" if market_price else "⚠️  No market data")
        print(f"📊 Comparables: {comparables_count} similar cars")
        print(f"🎯 Confidence: {confidence:.1%}")
        print()
        print(f"💰 ACTUAL Discount: {discount_pct:+.1f}%")
        print(f"⭐ Quality: {quality}")
        print(f"📈 Final Score: {score:.2f}/10.0")
        print(f"{'✅ WOULD POST TO TELEGRAM' if score >= 7.0 else '❌ Would NOT post (below 7.0)'}")
        print()
        print()

if __name__ == '__main__':
    main()
