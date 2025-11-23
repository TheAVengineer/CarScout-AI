#!/usr/bin/env python3
"""
Re-normalize listings with NULL brand/model

After populating brand_models table, this script triggers the normalize task
for all listings that have NULL brand_id or model_id.
"""
from sqlalchemy import create_engine, text
from configs.settings import settings
from workers.pipeline.tasks.normalize import normalize_listing

def main():
    engine = create_engine(settings.DATABASE_SYNC_URL)
    
    print("=" * 60)
    print("🔄 CarScout AI - Re-Normalize Listings")
    print("=" * 60)
    print()
    
    with engine.connect() as conn:
        # Count listings needing re-normalization
        null_listings = conn.execute(text("""
            SELECT ln.raw_id
            FROM listings_normalized ln
            WHERE (ln.brand_id IS NULL OR ln.model_id IS NULL)
              AND ln.is_duplicate = false
            LIMIT 10000
        """)).fetchall()
        
        total = len(null_listings)
        print(f"📊 Found {total:,} listings with NULL brand/model")
        print()
        
        if total == 0:
            print("✅ No listings need re-normalization!")
            return
        
        # Ask for confirmation
        print(f"⚠️  This will trigger {total:,} Celery tasks.")
        print(f"   Estimated time: {total * 0.2 / 60:.1f} minutes")
        print()
        
        response = input("Continue? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Cancelled.")
            return
        
        print()
        print("🚀 Triggering normalization tasks...")
        
        queued = 0
        errors = 0
        
        for (raw_id,) in null_listings:
            try:
                # Trigger normalize task with raw_id (as string)
                normalize_listing.delay(str(raw_id))
                queued += 1
                
                if queued % 1000 == 0:
                    print(f"    Queued {queued:,}/{total:,}...")
                    
            except Exception as e:
                print(f"    ⚠️  Error queueing {raw_id}: {e}")
                errors += 1
        
        print()
        print("✅ Tasks Queued!")
        print(f"  ✓ Queued: {queued:,}")
        print(f"  ✗ Errors: {errors:,}")
        print()
        print("⏳ Tasks are processing in the background.")
        print("   Check progress with:")
        print(f"   SELECT COUNT(*) FROM listings_normalized WHERE brand_id IS NOT NULL;")
        print()
        print("=" * 60)

if __name__ == "__main__":
    main()
