#!/usr/bin/env python3
"""
Trigger full pipeline for recently updated listings

This runs the complete pipeline:
1. Price - Find comparables and estimate market price
2. AI - Classify risk level
3. Score - Calculate deal score
4. Notify - Post to Telegram if approved

Run this after fixing brand/model data to get Telegram notifications working!
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from configs.settings import settings
from workers.pipeline.tasks.price import estimate_price

def main():
    """Trigger full pipeline for listings with brand/model"""
    engine = create_engine(settings.DATABASE_SYNC_URL)
    conn = engine.connect()
    
    print("🚀 Triggering FULL PIPELINE for listings with brand/model...")
    print("=" * 100)
    
    # Get listings that have brand/model and were recently updated
    query = text('''
    SELECT ln.id, ln.brand_id, ln.model_id, ln.year, ln.price_bgn
    FROM listings_normalized ln
    LEFT JOIN comps_cache cc ON cc.listing_id = ln.id
    WHERE ln.brand_id IS NOT NULL 
    AND ln.brand_id != ''
    AND ln.model_id IS NOT NULL
    AND ln.price_bgn IS NOT NULL
    AND ln.price_bgn > 500
    AND ln.updated_at > NOW() - INTERVAL '30 minutes'
    AND cc.id IS NULL
    ORDER BY ln.created_at DESC
    LIMIT 500
    ''')
    
    result = conn.execute(query)
    listings = result.fetchall()
    conn.close()
    
    if not listings:
        print("❌ No listings found that need pipeline processing!")
        print("   Listings must have: brand_id, model_id, price_bgn, and no comps_cache entry")
        return
    
    print(f"📊 Found {len(listings)} listings to process")
    print()
    print("Sample listings:")
    for i, listing in enumerate(listings[:10], 1):
        print(f"  {i}. {listing[1]} {listing[2]} {listing[3]} - {listing[4]:,} BGN")
    print()
    
    # Confirm
    response = input(f"⚠️  Trigger pipeline for {len(listings)} listings? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted")
        return
    
    print()
    print("🔧 Triggering pipeline tasks...")
    print("=" * 100)
    
    # Trigger price estimation (which chains to AI → score → notify)
    for i, listing in enumerate(listings, 1):
        listing_id = str(listing[0])
        estimate_price.delay(listing_id)
        
        if i % 50 == 0:
            print(f"  ✅ Queued {i}/{len(listings)} listings...")
    
    print(f"✅ Queued {len(listings)} pipeline tasks!")
    print()
    print("📊 Pipeline flow:")
    print("  1. ⚡ PRICE → Find comparables, estimate market price, save to comps_cache")
    print("  2. 🤖 AI → Classify risk level (low/medium/high)")
    print("  3. ⭐ SCORE → Calculate deal score (1-10)")
    print("  4. 📱 NOTIFY → If score ≥7.5 → POST TO TELEGRAM! 🎉")
    print()
    print("⏱️  Expected time: ~5-10 minutes for 500 listings")
    print()
    print("💡 Check Telegram channel in a few minutes!")
    print("💡 Monitor progress: tail -f logs/celery_worker.log | grep 'approved\\|Telegram'")

if __name__ == '__main__':
    main()
