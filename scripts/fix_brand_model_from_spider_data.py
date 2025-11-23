#!/usr/bin/env python3
"""
Fix brand/model in listings_normalized by copying from spider-extracted data in listings_raw.parsed_data

This script addresses the root cause where:
1. Spider correctly extracts brand/model and stores in listings_raw.parsed_data
2. Parse task never runs or ignores this data
3. listings_normalized ends up with NULL brand/model

Solution: Copy brand/model from parsed_data to listings_normalized directly
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from configs.settings import settings


def main():
    """Copy brand/model from listings_raw.parsed_data to listings_normalized"""
    engine = create_engine(settings.DATABASE_SYNC_URL)
    conn = engine.connect()
    
    print("🔍 Checking listings with NULL brand/model but spider data available...")
    print("=" * 100)
    
    # Find listings where spider extracted brand/model but it's NULL in normalized table
    query = text('''
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN lr.parsed_data->>'brand' IS NOT NULL THEN 1 END) as has_brand,
        COUNT(CASE WHEN lr.parsed_data->>'model' IS NOT NULL THEN 1 END) as has_model
    FROM listings_normalized ln
    JOIN listings_raw lr ON lr.id = ln.raw_id
    WHERE ln.brand_id IS NULL
    AND lr.parsed_data IS NOT NULL
    ''')
    
    result = conn.execute(query).fetchone()
    print(f"Total NULL brand/model listings: {result[0]:,}")
    print(f"  - Have brand in spider data: {result[1]:,}")
    print(f"  - Have model in spider data: {result[2]:,}")
    print()
    
    if result[0] == 0:
        print("✅ No listings need fixing!")
        conn.close()
        return
    
    # Show sample of what will be fixed
    print("📋 Sample of listings to fix:")
    print("-" * 100)
    sample_query = text('''
    SELECT 
        ln.id,
        ln.title,
        ln.brand_id as current_brand,
        ln.model_id as current_model,
        lr.parsed_data->>'brand' as spider_brand,
        lr.parsed_data->>'model' as spider_model
    FROM listings_normalized ln
    JOIN listings_raw lr ON lr.id = ln.raw_id
    WHERE ln.brand_id IS NULL
    AND lr.parsed_data IS NOT NULL
    LIMIT 10
    ''')
    
    samples = conn.execute(sample_query).fetchall()
    for row in samples:
        print(f"Title: {row[1][:50]}")
        print(f"  Current: brand={row[2]}, model={row[3]}")
        print(f"  Spider:  brand={row[4]}, model={row[5]}")
        print()
    
    # Ask for confirmation
    response = input(f"\n⚠️  Update {result[0]:,} listings with spider-extracted brand/model? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted")
        conn.close()
        return
    
    print("\n🔧 Updating listings...")
    print("=" * 100)
    
    # Update listings - copy brand/model from parsed_data to brand_id/model_id
    update_query = text('''
    UPDATE listings_normalized ln
    SET 
        brand_id = lr.parsed_data->>'brand',
        model_id = lr.parsed_data->>'model',
        updated_at = NOW()
    FROM listings_raw lr
    WHERE lr.id = ln.raw_id
    AND ln.brand_id IS NULL
    AND lr.parsed_data IS NOT NULL
    AND lr.parsed_data->>'brand' IS NOT NULL
    ''')
    
    result = conn.execute(update_query)
    conn.commit()
    
    updated_count = result.rowcount
    print(f"✅ Updated {updated_count:,} listings!")
    print()
    
    # Verify the update
    verify_query = text('''
    SELECT 
        COUNT(*) as still_null,
        COUNT(CASE WHEN brand_id IS NOT NULL THEN 1 END) as now_has_brand
    FROM listings_normalized
    ''')
    
    verify_result = conn.execute(verify_query).fetchone()
    print("📊 After update:")
    print(f"  - Total listings: {verify_result[0] + verify_result[1]:,}")
    print(f"  - With brand/model: {verify_result[1]:,}")
    print(f"  - Still NULL: {verify_result[0]:,}")
    print()
    
    conn.close()
    
    print("✅ Done! Next steps:")
    print("  1. Run normalize task to standardize the brand/model values")
    print("  2. Run price task to find comparables")
    print("  3. Run score task to calculate deal scores")
    print("  4. Check for Telegram notifications!")
    print()
    print("💡 Tip: You can trigger re-scoring with:")
    print("   python scripts/renormalize_listings.py")


if __name__ == '__main__':
    main()
