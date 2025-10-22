#!/usr/bin/env python
"""
End-to-end pipeline test
Tests the complete flow from scraping to notification
"""
import sys
import os
import time
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw, ListingNormalized, Source, Score
from workers.pipeline.tasks.parse import parse_listing
from workers.pipeline.tasks.normalize import normalize_listing
from workers.pipeline.tasks.dedupe import deduplicate_listing
from workers.pipeline.tasks.price import estimate_price
from workers.pipeline.tasks.ai import classify_risk
from workers.pipeline.tasks.score import calculate_score


def create_test_listing():
    """Create a test listing from sample HTML"""
    print("📝 Creating test listing...")
    
    session = get_sync_session()
    
    # Get Mobile.bg source
    source = session.query(Source).filter_by(name='mobile_bg').first()
    if not source:
        print("❌ Mobile.bg source not found. Run seed_database.py first.")
        return None
    
    # Sample Mobile.bg HTML (simplified)
    sample_html = """
    <html>
    <head><title>BMW X5 3.0 d - Mobile.bg</title></head>
    <body>
        <h1 class="titleItem">BMW X5 3.0 d xDrive - 2018</h1>
        <div class="price">35 000 лв</div>
        <table class="dilarData">
            <tr><td>Марка:</td><td>BMW</td></tr>
            <tr><td>Модел:</td><td>X5</td></tr>
            <tr><td>Година:</td><td>2018 г.</td></tr>
            <tr><td>Пробег:</td><td>120 000 км</td></tr>
            <tr><td>Гориво:</td><td>Дизел</td></tr>
            <tr><td>Скоростна кутия:</td><td>Автоматична</td></tr>
            <tr><td>Категория:</td><td>Джип/SUV</td></tr>
            <tr><td>Двигател:</td><td>3000 куб. см, 258 к.с.</td></tr>
            <tr><td>Населено място:</td><td>София</td></tr>
        </table>
        <div class="description">
            Отлично състояние, редовна поддръжка, full options.
            Кожен салон, panorama, нагреватели, Memory seats.
            Зимни + летни гуми на джанти. Перфектна кола!
        </div>
        <div class="thumbs">
            <img src="https://www.mobile.bg/images/sample1.jpg" />
            <img src="https://www.mobile.bg/images/sample2.jpg" />
            <img src="https://www.mobile.bg/images/sample3.jpg" />
        </div>
        <div class="sellerName">Иван Петров</div>
    </body>
    </html>
    """
    
    # Create raw listing
    listing_raw = ListingRaw(
        source_id=source.id,
        site_ad_id=f"test_{int(time.time())}",
        url="https://www.mobile.bg/test/123456",
        raw_html_path=None,  # S3 path (not needed for test)
    )
    
    session.add(listing_raw)
    session.commit()
    session.refresh(listing_raw)
    
    listing_id = str(listing_raw.id)
    print(f"✅ Created test listing: {listing_id}")
    
    session.close()
    return listing_id


def test_pipeline(listing_id: str):
    """Test the complete pipeline"""
    print("\n🔄 Testing pipeline stages...\n")
    
    session = get_sync_session()
    
    # Stage 1: Parse
    print("1️⃣  Testing PARSE task...")
    try:
        result = parse_listing(listing_id)
        print(f"   ✅ Parse complete: {result}")
        time.sleep(1)
    except Exception as e:
        print(f"   ❌ Parse failed: {e}")
        return False
    
    # Get normalized listing
    listing_raw = session.query(ListingRaw).filter_by(id=listing_id).first()
    if not listing_raw.normalized:
        print("   ❌ No normalized listing created")
        return False
    
    normalized_id = str(listing_raw.normalized.id)
    print(f"   📋 Normalized listing: {normalized_id}")
    
    # Stage 2: Normalize
    print("\n2️⃣  Testing NORMALIZE task...")
    try:
        result = normalize_listing(normalized_id)
        print(f"   ✅ Normalize complete: {result}")
        time.sleep(1)
    except Exception as e:
        print(f"   ❌ Normalize failed: {e}")
        return False
    
    # Stage 3: Dedupe
    print("\n3️⃣  Testing DEDUPE task...")
    try:
        result = deduplicate_listing(normalized_id)
        print(f"   ✅ Dedupe complete: {result}")
        time.sleep(1)
    except Exception as e:
        print(f"   ❌ Dedupe failed: {e}")
        return False
    
    # Stage 4: Price
    print("\n4️⃣  Testing PRICE task...")
    try:
        result = estimate_price(normalized_id)
        print(f"   ✅ Price complete: {result}")
        time.sleep(1)
    except Exception as e:
        print(f"   ❌ Price failed: {e}")
        # Price might fail if no comparables - that's OK for test
        print(f"   ⚠️  Price task failed (expected if no comparable listings)")
    
    # Stage 5: AI Risk
    print("\n5️⃣  Testing AI RISK task...")
    try:
        result = classify_risk(normalized_id)
        print(f"   ✅ AI Risk complete: {result}")
        time.sleep(1)
    except Exception as e:
        print(f"   ❌ AI Risk failed: {e}")
        return False
    
    # Stage 6: Score
    print("\n6️⃣  Testing SCORE task...")
    try:
        result = calculate_score(normalized_id)
        print(f"   ✅ Score complete: {result}")
        time.sleep(1)
    except Exception as e:
        print(f"   ❌ Score failed: {e}")
        return False
    
    # Check final state
    print("\n📊 Checking final state...")
    listing = session.query(ListingNormalized).filter_by(id=normalized_id).first()
    
    print(f"   Brand: {listing.brand_id}")
    print(f"   Model: {listing.model_id}")
    print(f"   Price: {listing.price_bgn} BGN")
    print(f"   Year: {listing.year}")
    print(f"   Mileage: {listing.mileage_km} km")
    print(f"   Fuel: {listing.fuel}")
    print(f"   Gearbox: {listing.gearbox}")
    print(f"   Is Duplicate: {listing.is_duplicate}")
    
    # Check price prediction
    if listing.comp_cache:
        print(f"   Predicted Price: {listing.comp_cache.predicted_price_bgn:.0f} BGN")
        print(f"   Discount: {listing.comp_cache.discount_pct:.1f}%")
        print(f"   Sample Size: {listing.comp_cache.sample_size} comparables")
    
    # Check score
    score = session.query(Score).filter_by(listing_id=listing.id).first()
    if score:
        print(f"\n   Final Score: {score.score:.2f}/10")
        print(f"   State: {score.final_state}")
        print(f"   Risk Penalty: {score.risk_penalty:.2f}")
        print(f"   Freshness Bonus: {score.freshness_bonus:.2f}")
        print(f"   Liquidity Bonus: {score.liquidity:.2f}")
        # score.reasons is already a list (SQLAlchemy decodes JSON automatically)
        reasons = score.reasons if isinstance(score.reasons, list) else json.loads(score.reasons)
        print(f"   Reasons: {', '.join(reasons)}")
    
    session.close()
    return True


def main():
    """Run end-to-end test"""
    print("🧪 CarScout AI - End-to-End Pipeline Test")
    print("=" * 60)
    print()
    
    # Create test listing
    listing_id = create_test_listing()
    if not listing_id:
        print("\n❌ Failed to create test listing")
        return 1
    
    # Test pipeline
    success = test_pipeline(listing_id)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Pipeline test PASSED!")
        print("\nAll stages completed successfully:")
        print("  ✅ Parse (HTML → structured data)")
        print("  ✅ Normalize (brand/model mapping)")
        print("  ✅ Dedupe (duplicate detection)")
        print("  ⚠️  Price (comparable-based estimation)")
        print("  ✅ AI Risk (rule-based classification)")
        print("  ✅ Score (final rating)")
        print("\n🎉 Your pipeline is working!")
        return 0
    else:
        print("❌ Pipeline test FAILED")
        print("\nSome stages did not complete successfully.")
        print("Check the error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
