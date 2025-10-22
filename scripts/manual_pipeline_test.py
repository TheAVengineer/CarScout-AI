"""
Manually run the complete pipeline on a test listing to demonstrate score improvement.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from libs.domain.database import sync_engine
from libs.domain.models import ListingRaw
from workers.pipeline.tasks.parse import parse_listing
from workers.pipeline.tasks.normalize import normalize_listing
from workers.pipeline.tasks.dedupe import check_duplicates
from workers.pipeline.tasks.price import estimate_price
from workers.pipeline.tasks.ai import classify_risk
from workers.pipeline.tasks.score import calculate_score

def run_pipeline_on_listing(url_pattern: str):
    """Run complete pipeline on a listing"""
    print(f"\n{'='*70}")
    print(f"RUNNING PIPELINE FOR: {url_pattern}")
    print(f"{'='*70}\n")
    
    with Session(sync_engine) as session:
        # Get the listing
        raw = session.query(ListingRaw).filter(
            ListingRaw.url.like(url_pattern),
            ListingRaw.raw_html.isnot(None)
        ).first()
        
        if not raw:
            print(f"❌ No listing found matching {url_pattern}")
            return
        
        print(f"URL: {raw.url}\n")
        
        # Stage 1: Parse
        print("▶ Stage 1: Parse HTML...")
        normalized_id = parse_listing(raw.id)
        if not normalized_id:
            print("❌ Parse failed!")
            return
        print(f"✅ Created normalized listing: {normalized_id}\n")
        
        # Stage 2: Normalize
        print("▶ Stage 2: Normalize brands/models...")
        normalize_listing(normalized_id)
        print(f"✅ Normalization complete\n")
        
        # Check the normalized listing
        from libs.domain.models import ListingNormalized
        normalized = session.query(ListingNormalized).filter(
            ListingNormalized.id == normalized_id
        ).first()
        
        print(f"📊 EXTRACTED DATA:")
        print(f"  Brand:      {normalized.brand.name if normalized.brand else 'None'}")
        print(f"  Model:      {normalized.model.name if normalized.model else 'None'}")
        print(f"  Year:       {normalized.year}")
        print(f"  Price:      {normalized.price_bgn} BGN")
        print(f"  Mileage:    {normalized.mileage_km} km")
        print(f"  Fuel:       {normalized.fuel}")
        print(f"  Gearbox:    {normalized.gearbox}")
        print()
        
        # Stage 3: Dedupe
        print("▶ Stage 3: Check for duplicates...")
        check_duplicates(normalized_id)
        session.refresh(normalized)
        print(f"✅ Is duplicate: {normalized.is_duplicate}\n")
        
        # Stage 4: Price
        print("▶ Stage 4: Estimate price...")
        estimate_price(normalized_id)
        print(f"✅ Price estimation complete\n")
        
        # Check price cache
        from libs.domain.models import CompsCache
        price_cache = session.query(CompsCache).filter(
            CompsCache.listing_id == normalized_id
        ).first()
        
        if price_cache:
            print(f"💰 PRICE ESTIMATION:")
            print(f"  Predicted:  {price_cache.predicted_price_bgn:.2f} BGN")
            print(f"  Discount:   {price_cache.discount_pct:.1f}%")
            print(f"  Comparables: {price_cache.sample_size} listings")
            print(f"  P10:        {price_cache.p10:.2f} BGN")
            print(f"  P50:        {price_cache.p50:.2f} BGN")
            print(f"  P90:        {price_cache.p90:.2f} BGN")
            print()
        
        # Stage 5: Risk
        print("▶ Stage 5: Classify risk...")
        classify_risk(normalized_id)
        print(f"✅ Risk classification complete\n")
        
        # Stage 6: Score
        print("▶ Stage 6: Calculate score...")
        calculate_score(normalized_id)
        print(f"✅ Scoring complete\n")
        
        # Get final score
        from libs.domain.models import Score
        score = session.query(Score).filter(
            Score.listing_id == normalized_id
        ).first()
        
        if score:
            print(f"{'='*70}")
            print(f"🎯 FINAL SCORE")
            print(f"{'='*70}")
            print(f"  Score:          {score.score:.2f}/10")
            print(f"  State:          {score.final_state}")
            print(f"  Risk Penalty:   {score.risk_penalty:.2f}")
            print(f"  Freshness Bonus: {score.freshness_bonus:.2f}")
            print(f"  Liquidity:      {score.liquidity:.2f}")
            print(f"\n  Reasons:")
            for reason in score.reasons:
                print(f"    • {reason}")
            print(f"{'='*70}\n")
        
        session.commit()

if __name__ == "__main__":
    # Test with the Audi A4 listing
    run_pipeline_on_listing('%audi-a4-s-line-kozha%')
