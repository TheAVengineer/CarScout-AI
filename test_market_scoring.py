#!/usr/bin/env python
"""
Quick Test: Score recent listings with market-aware system
This bypasses Celery and runs tasks directly for immediate testing
"""
from workers.pipeline.tasks.market_score import market_aware_score
from sqlalchemy import create_engine, text
from configs.settings import settings
from datetime import datetime, timedelta

def main():
    print('🧪 DIRECT MARKET-AWARE SCORING TEST')
    print('='*60)
    print()
    
    # Connect to database
    engine = create_engine(settings.DATABASE_SYNC_URL)
    conn = engine.connect()
    
    # Get recent unscored listings
    query = text('''
        SELECT ln.id, ln.brand_id, ln.model_id, ln.title, ln.price_bgn, ln.year
        FROM listings_normalized ln
        LEFT JOIN scores s ON s.listing_id = ln.id
        WHERE ln.created_at >= :cutoff
        AND ln.brand_id IS NOT NULL
        AND ln.model_id IS NOT NULL
        AND ln.price_bgn IS NOT NULL
        AND s.id IS NULL
        LIMIT 5
    ''')
    
    cutoff = datetime.now() - timedelta(days=30)
    listings = conn.execute(query, {'cutoff': cutoff}).fetchall()
    conn.close()
    
    print(f'Found {len(listings)} unscored listings from last 30 days')
    print()
    
    approved = 0
    rejected = 0
    
    for listing in listings:
        print(f'\n📋 {listing.year} {listing.title} - {listing.price_bgn:,.0f} BGN')
        print(f'   ID: {listing.id}')
        
        try:
            # Run task directly (not through Celery)
            result = market_aware_score.run(str(listing.id))
            
            score = result['score']
            should_post = result['should_post']
            comparables = result['comparable_count']
            discount = result['discount_pct']
            
            if should_post:
                print(f'   ✅ Score: {score}/10 → APPROVED FOR TELEGRAM')
                approved += 1
            else:
                print(f'   ❌ Score: {score}/10 → REJECTED')
                rejected += 1
            
            print(f'   📊 Comparables: {comparables}, Discount: {discount:.1f}%')
            
        except Exception as e:
            print(f'   ⚠️  Error: {e}')
            rejected += 1
    
    print()
    print('='*60)
    print(f'✅ RESULTS: {approved} approved, {rejected} rejected')
    print('='*60)
    
    if approved > 0:
        print()
        print('📱 Approved listings will be posted to Telegram!')
        print('   Check channel: https://t.me/your_channel')

if __name__ == '__main__':
    main()
