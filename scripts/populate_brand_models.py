#!/usr/bin/env python3
"""
Populate brand_models table from scraped data

This script extracts unique brand/model combinations from listings_normalized
and populates the brand_models reference table. This is CRITICAL for:
1. Brand/model normalization to work
2. Finding comparable vehicles for pricing
3. Scoring listings properly
4. Getting Telegram notifications for good deals
"""
import uuid
import re
from sqlalchemy import create_engine, text
from configs.settings import settings

def main():
    engine = create_engine(settings.DATABASE_SYNC_URL)
    
    print("=" * 60)
    print("🔧 CarScout AI - Brand/Model Mapper")
    print("=" * 60)
    print()
    
    with engine.connect() as conn:
        # Check current state
        current_count = conn.execute(text(
            "SELECT COUNT(*) FROM brand_models WHERE active = true"
        )).scalar()
        
        null_count = conn.execute(text("""
            SELECT COUNT(*) FROM listings_normalized 
            WHERE brand_id IS NULL OR model_id IS NULL
        """)).scalar()
        
        print(f"📊 Current State:")
        print(f"  Brand/model mappings: {current_count:,}")
        print(f"  Listings with NULL brand/model: {null_count:,}")
        print()
        
        # Extract unique brand/model combinations
        print("🔍 Extracting unique brand/model combinations...")
        
        combos = conn.execute(text("""
            SELECT DISTINCT
                ln.brand_id as brand_raw,
                ln.model_id as model_raw,
                COUNT(*) as listing_count
            FROM listings_normalized ln
            WHERE ln.brand_id IS NOT NULL 
              AND ln.model_id IS NOT NULL
              AND ln.brand_id != ''
              AND ln.model_id != ''
              AND ln.brand_id != 'None'
              AND ln.model_id != 'None'
            GROUP BY ln.brand_id, ln.model_id
            HAVING COUNT(*) >= 2
            ORDER BY COUNT(*) DESC
            LIMIT 1000
        """)).fetchall()
        
        print(f"  Found {len(combos)} unique combinations (with 2+ listings each)")
        print()
        
        # Insert into brand_models
        print("💾 Inserting into brand_models table...")
        
        inserted = 0
        skipped = 0
        errors = 0
        
        for brand_raw, model_raw, count in combos:
            # Clean and normalize
            brand_clean = re.sub(r'[^\w\s-]', '', str(brand_raw)).strip().lower()
            model_clean = re.sub(r'[^\w\s-]', '', str(model_raw)).strip().lower()
            
            # Skip invalid entries
            if (not brand_clean or not model_clean or 
                brand_clean == 'unknown' or model_clean == 'unknown' or
                len(brand_clean) < 2 or len(model_clean) < 1):
                skipped += 1
                continue
            
            # Check if exists (case-insensitive)
            exists = conn.execute(text("""
                SELECT 1 FROM brand_models 
                WHERE LOWER(brand) = LOWER(:brand) 
                  AND LOWER(model) = LOWER(:model)
            """), {"brand": brand_raw, "model": model_raw}).fetchone()
            
            if not exists:
                try:
                    # Generate UUID and insert
                    new_id = uuid.uuid4()
                    conn.execute(text("""
                        INSERT INTO brand_models (
                            id, brand, model, normalized_brand, normalized_model, active
                        ) VALUES (
                            :id, :brand, :model, :norm_brand, :norm_model, true
                        )
                    """), {
                        "id": new_id,
                        "brand": brand_raw,
                        "model": model_raw,
                        "norm_brand": brand_clean,
                        "norm_model": model_clean
                    })
                    conn.commit()
                    inserted += 1
                    
                    if inserted % 100 == 0:
                        print(f"    Inserted {inserted}...")
                        
                except Exception as e:
                    print(f"    ⚠️  Error: {brand_raw}/{model_raw}: {e}")
                    conn.rollback()
                    errors += 1
            else:
                skipped += 1
        
        print()
        print("✅ Insertion Complete!")
        print(f"  ✓ Inserted: {inserted:,}")
        print(f"  ⊘ Skipped (duplicates): {skipped:,}")
        print(f"  ✗ Errors: {errors:,}")
        print()
        
        # Show final state
        final_count = conn.execute(text(
            "SELECT COUNT(*) FROM brand_models WHERE active = true"
        )).scalar()
        
        print(f"📊 Final State:")
        print(f"  Total brand/model mappings: {final_count:,}")
        print()
        
        # Show top brands
        print("🏆 Top 10 Brands by Model Count:")
        top_brands = conn.execute(text("""
            SELECT normalized_brand, COUNT(*) as model_count
            FROM brand_models
            WHERE active = true
            GROUP BY normalized_brand
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)).fetchall()
        
        for brand, count in top_brands:
            print(f"    {brand}: {count} models")
        print()
        
        print("=" * 60)
        print("🎉 Done! Now run the re-normalization script.")
        print("=" * 60)

if __name__ == "__main__":
    main()
