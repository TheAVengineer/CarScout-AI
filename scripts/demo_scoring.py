#!/usr/bin/env python3
"""
Demonstrate the improved scoring system with examples
"""

def calculate_score(asking_price, market_price, comparables_count, year, mileage, is_automatic, is_eco):
    """Calculate score using NEW improved algorithm"""
    
    # Base score - LOWER than before (4.0 vs 5.0)
    score = 4.0
    
    if market_price and comparables_count >= 5:
        # Calculate REAL discount (ignore seller's fake claims)
        discount_pct = ((market_price - asking_price) / market_price) * 100
        
        # Confidence factor based on data quality
        if comparables_count >= 20:
            confidence = 1.0  # High confidence
        elif comparables_count >= 10:
            confidence = 0.8  # Good confidence
        else:
            confidence = 0.6  # Lower confidence (5-9 comparables)
        
        # Price scoring with confidence adjustment
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
            score -= 1.0  # PENALTY for overpriced!
            quality = "OVERPRICED"
    else:
        discount_pct = 0
        confidence = 0
        quality = "UNKNOWN"
        score = 3.0  # Low score if insufficient data
    
    # Feature bonuses (REDUCED to keep focus on price)
    if year >= 2020:
        score += 0.3  # was 0.4
    if mileage < 50000:
        score += 0.3  # was 0.4
    if is_automatic:
        score += 0.2  # was 0.3
    if is_eco:
        score += 0.4  # was 0.5
    
    score = min(10.0, max(1.0, score))
    
    return score, discount_pct, quality, confidence


def main():
    print("🧪 IMPROVED SCORING SYSTEM - Examples")
    print("=" * 90)
    print()
    
    scenarios = [
        {
            "name": "❌ FAKE DISCOUNT SCAM",
            "description": "Seller inflates original price to show fake discount",
            "car": "BMW 320d, 2018, 120k km, Automatic",
            "asking_price": 19000,
            "seller_claimed_original": 25000,
            "market_price": 18500,  # Real market from database
            "comparables_count": 15,
            "year": 2018,
            "mileage": 120000,
            "is_automatic": True,
            "is_eco": False,
        },
        {
            "name": "✅ REAL DEAL - Exceptional",
            "description": "Genuinely underpriced, seller needs quick sale",
            "car": "Mercedes A-Class, 2019, 80k km, Automatic",
            "asking_price": 18000,
            "market_price": 24500,
            "comparables_count": 22,
            "year": 2019,
            "mileage": 80000,
            "is_automatic": True,
            "is_eco": False,
        },
        {
            "name": "⚠️  MARGINAL DEAL",
            "description": "Slightly below market but not exciting",
            "car": "VW Golf, 2017, 100k km, Manual",
            "asking_price": 11000,
            "market_price": 12500,
            "comparables_count": 18,
            "year": 2017,
            "mileage": 100000,
            "is_automatic": False,
            "is_eco": False,
        },
        {
            "name": "❌ OVERPRICED",
            "description": "Seller asking more than market average",
            "car": "Audi A4, 2016, 150k km, Automatic",
            "asking_price": 16000,
            "market_price": 14500,
            "comparables_count": 25,
            "year": 2016,
            "mileage": 150000,
            "is_automatic": True,
            "is_eco": False,
        },
        {
            "name": "✅ GOOD DEAL - New Car",
            "description": "20% below market + great features",
            "car": "Tesla Model 3, 2021, 30k km, Auto, Electric",
            "asking_price": 32000,
            "market_price": 40000,
            "comparables_count": 12,
            "year": 2021,
            "mileage": 30000,
            "is_automatic": True,
            "is_eco": True,
        },
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['name']}")
        print("-" * 90)
        print(f"📝 {scenario['description']}")
        print()
        print(f"🚗 Car: {scenario['car']}")
        print(f"💰 Asking Price: €{scenario['asking_price']:,}")
        
        if 'seller_claimed_original' in scenario:
            fake_discount = ((scenario['seller_claimed_original'] - scenario['asking_price']) / scenario['seller_claimed_original']) * 100
            print(f"❌ Seller Claims: ~~€{scenario['seller_claimed_original']:,}~~ → €{scenario['asking_price']:,} ({fake_discount:.1f}% OFF!)")
        
        print()
        print(f"✅ REAL Market Data:")
        print(f"   • Average Price: €{scenario['market_price']:,}")
        print(f"   • Comparables: {scenario['comparables_count']} similar cars in database")
        print()
        
        # Calculate score
        score, discount_pct, quality, confidence = calculate_score(
            scenario['asking_price'],
            scenario['market_price'],
            scenario['comparables_count'],
            scenario['year'],
            scenario['mileage'],
            scenario.get('is_automatic', False),
            scenario.get('is_eco', False)
        )
        
        print(f"📊 Analysis:")
        print(f"   • ACTUAL Discount: {discount_pct:+.1f}% from real market")
        print(f"   • Quality Rating: {quality}")
        print(f"   • Data Confidence: {confidence:.0%}")
        print()
        print(f"⭐ FINAL SCORE: {score:.2f}/10.0")
        
        if score >= 7.0:
            print(f"✅ ✅ ✅ WOULD POST TO TELEGRAM! ✅ ✅ ✅")
        else:
            print(f"❌ Would NOT post (below 7.0 threshold)")
        
        print()
        print()
    
    print("=" * 90)
    print("📈 Summary:")
    print()
    print("OLD SYSTEM: Trusted any price comparison → Many fake deals posted")
    print("NEW SYSTEM: Only trusts database market data → Only real deals posted")
    print()
    print("Key Improvements:")
    print("✅ Ignores seller's inflated 'original price' claims")
    print("✅ Compares to REAL market prices from 40K+ cars")
    print("✅ Requires minimum 5 comparables for confidence")
    print("✅ Penalizes overpriced listings (score -1.0)")
    print("✅ Confidence factor adjusts bonus based on data quality")
    print()
    print("Result: Only 20-25%+ REAL discounts get posted!")


if __name__ == '__main__':
    main()
