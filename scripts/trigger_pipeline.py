"""
Manually trigger pipeline on a specific listing to demonstrate score improvements.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from libs.domain.database import sync_engine
from libs.domain.models import ListingRaw
import time

# Import Celery app to call tasks via Celery (uses latest code from worker)
from workers.pipeline import celery_app
from workers.pipeline.tasks import parse, normalize, dedupe, price, ai, score

print("\n" + "="*70)
print("MANUALLY TRIGGERING PIPELINE ON AUDI A4 LISTING")
print("="*70 + "\n")

with Session(sync_engine) as session:
    # Get the Audi A4 listing with real HTML
    raw = session.query(ListingRaw).filter(
        ListingRaw.url.like('%audi-a4-s-line-kozha%'),
        ListingRaw.raw_html.isnot(None)
    ).first()
    
    if not raw:
        print("❌ Listing not found!")
        sys.exit(1)
    
    print(f"📍 Found listing: {raw.url}\n")
    print(f"▶ Starting pipeline...\n")
    
    try:
        # Call each task via Celery (uses latest code from restarted worker)
        print("  [1/6] Parsing HTML...")
        result = parse.parse_listing.delay(str(raw.id))
        result.get(timeout=30)  # Wait for completion
        print(f"      ✅ Parse complete\n")
        
        # Give DB a moment to commit
        time.sleep(1)
        
        # Get the normalized listing that was created
        from libs.domain.models import ListingNormalized
        session.expire_all()  # Force refresh from DB
        normalized = session.query(ListingNormalized).filter(
            ListingNormalized.raw_id == raw.id
        ).first()
        
        if not normalized:
            print("❌ No normalized listing created!")
            sys.exit(1)
        
        normalized_id = normalized.id
        print(f"      Normalized ID: {normalized_id}\n")
        
        print("  [2/6] Normalizing brand/model...")
        result = normalize.normalize_listing.delay(str(raw.id))
        result.get(timeout=30)
        print(f"      ✅ Normalization complete\n")
        
        time.sleep(1)
        
        print("  [3/6] Checking for duplicates...")
        result = dedupe.deduplicate_listing.delay(str(normalized_id))
        result.get(timeout=30)
        print(f"      ✅ Deduplication complete\n")
        
        time.sleep(1)
        
        print("  [4/6] Estimating price...")
        result = price.estimate_price.delay(str(normalized_id))
        result.get(timeout=30)
        print(f"      ✅ Price estimation complete\n")
        
        time.sleep(1)
        
        print("  [5/6] Classifying risk...")
        result = ai.classify_risk.delay(str(normalized_id))
        result.get(timeout=30)
        print(f"      ✅ Risk classification complete\n")
        
        time.sleep(1)
        
        print("  [6/6] Calculating score...")
        result = score.calculate_score.delay(str(normalized_id))
        result.get(timeout=30)
        print(f"      ✅ Scoring complete\n")
        
        # Get the final results
        from libs.domain.models import Score, CompCache
        
        # Refresh to get updated data
        session.refresh(normalized)
        
        score = session.query(Score).filter(
            Score.listing_id == normalized_id
        ).first()
        
        price_cache = session.query(CompCache).filter(
            CompCache.listing_id == normalized_id
        ).first()
        
        # Display results
        print("="*70)
        print("📊 RESULTS")
        print("="*70)
        print(f"\n✅ EXTRACTED DATA:")
        print(f"  Brand:      {normalized.brand_id}")
        print(f"  Model:      {normalized.model_id}")
        print(f"  Year:       {normalized.year}")
        print(f"  Price:      {normalized.price_bgn} BGN")
        print(f"  Mileage:    {normalized.mileage_km} km")
        print(f"  Duplicate:  {normalized.is_duplicate}")
        
        if price_cache:
            print(f"\n💰 PRICE ESTIMATION:")
            print(f"  Predicted:  {price_cache.predicted_price_bgn:.2f} BGN")
            print(f"  Discount:   {price_cache.discount_pct:.1f}%")
            print(f"  Comparables: {price_cache.sample_size} listings")
        
        if score:
            print(f"\n🎯 FINAL SCORE:")
            print(f"  Score:      {score.score:.2f}/10")
            print(f"  State:      {score.final_state}")
            print(f"  Risk:       {score.risk_penalty:.2f}")
            print(f"  Freshness:  {score.freshness_bonus:.2f}")
            print(f"  Liquidity:  {score.liquidity:.2f}")
            print(f"\n  Reasons:")
            for reason in score.reasons:
                print(f"    • {reason}")
        
        print("\n" + "="*70 + "\n")
        print("✅ Pipeline completed successfully!")
        print(f"   The listing scored {score.score}/10 and was {score.final_state}!\n")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
