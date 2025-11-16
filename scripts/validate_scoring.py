#!/usr/bin/env python3
"""
Validation Script - Test Enhanced Scoring on Real Examples

This script:
1. Samples random listings from database
2. Calculates scores using enhanced algorithm
3. Shows why each listing got its score
4. Helps validate if scoring is accurate
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import logging

from configs.settings import settings
from workers.pipeline.tasks.database_monitor_enhanced import _evaluate_listing_enhanced, _get_enhanced_comparables

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def sample_and_validate(limit=20):
    """
    Sample random listings and show their scores with explanations
    """
    logger.info("="*80)
    logger.info("🔍 CARSCOUT ENHANCED SCORING VALIDATION")
    logger.info("="*80)
    logger.info("")
    
    # Create database connection
    engine = create_engine(settings.DATABASE_SYNC_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get random sample of active listings with required fields
    sql = """
        SELECT 
            site_ad_id,
            url,
            parsed_data->>'brand' as brand,
            parsed_data->>'model' as model,
            CAST(parsed_data->>'year' AS INTEGER) as year,
            CAST(parsed_data->>'price' AS INTEGER) as price,
            CAST(parsed_data->>'mileage_km' AS INTEGER) as mileage_km,
            parsed_data->>'fuel' as fuel,
            parsed_data->>'gearbox' as gearbox,
            first_seen_at,
            updated_at
        FROM listings_raw
        WHERE is_active = true
            AND parsed_data->>'brand' IS NOT NULL
            AND parsed_data->>'model' IS NOT NULL
            AND parsed_data->>'year' IS NOT NULL
            AND parsed_data->>'price' IS NOT NULL
            AND parsed_data->>'mileage_km' IS NOT NULL
            AND CAST(parsed_data->>'price' AS INTEGER) > 500
            AND CAST(parsed_data->>'mileage_km' AS INTEGER) < 250000
        ORDER BY RANDOM()
        LIMIT :limit
    """
    
    result = session.execute(text(sql), {'limit': limit})
    listings = result.fetchall()
    
    logger.info(f"📊 Sampled {len(listings)} random listings from database\n")
    
    scores = []
    
    for i, listing in enumerate(listings, 1):
        site_ad_id, url, brand, model, year, price, mileage_km, fuel, gearbox, first_seen, updated = listing
        
        logger.info(f"\n{'='*80}")
        logger.info(f"LISTING #{i}")
        logger.info(f"{'='*80}")
        logger.info(f"🚗 {brand} {model} ({year})")
        logger.info(f"💰 Price: {price:,} BGN")
        logger.info(f"📏 Mileage: {mileage_km:,} km")
        logger.info(f"⛽ Fuel: {fuel or 'N/A'}")
        logger.info(f"⚙️  Gearbox: {gearbox or 'N/A'}")
        logger.info(f"🔗 URL: {url}")
        logger.info(f"")
        
        # Calculate score using enhanced algorithm
        score_result = _evaluate_listing_enhanced(
            session,
            site_ad_id,
            brand, model, year, price, mileage_km, fuel, gearbox,
            first_seen, updated
        )
        
        if score_result:
            score = score_result['score']
            avg_price = score_result.get('avg_price')
            discount_pct = score_result.get('discount_pct', 0)
            comp_count = score_result.get('comp_count', 0)
            days_on_market = score_result.get('days_on_market', 0)
            reasons = score_result.get('reasons', [])
            
            scores.append(score)
            
            # Color code based on score
            if score >= 8.3:
                emoji = "🎯 EXCELLENT DEAL!"
            elif score >= 7.5:
                emoji = "✅ VERY GOOD"
            elif score >= 6.5:
                emoji = "👍 GOOD"
            elif score >= 5.5:
                emoji = "😐 AVERAGE"
            else:
                emoji = "❌ BELOW AVERAGE"
            
            logger.info(f"{emoji}")
            logger.info(f"📊 SCORE: {score:.2f}/10")
            logger.info(f"")
            
            if avg_price:
                logger.info(f"Market Analysis:")
                logger.info(f"  • Average market price: {avg_price:,.0f} BGN")
                logger.info(f"  • This listing: {price:,} BGN")
                logger.info(f"  • Discount: {discount_pct:.1f}%")
                logger.info(f"  • Based on {comp_count} comparable listings")
                logger.info(f"  • Days on market: {days_on_market}")
                logger.info(f"")
            
            logger.info(f"Why this score:")
            for reason in reasons:
                logger.info(f"  ✓ {reason}")
            
            # Manual validation prompt
            if score >= 8.3:
                logger.info(f"")
                logger.info(f"🤔 VALIDATION: Would you consider this a good deal? (Check the URL)")
        else:
            logger.info(f"⚠️  Could not evaluate (insufficient market data)")
        
        logger.info("")
    
    # Summary statistics
    session.close()
    
    if scores:
        logger.info(f"\n{'='*80}")
        logger.info(f"SUMMARY STATISTICS")
        logger.info(f"{'='*80}")
        logger.info(f"Total evaluated: {len(scores)}")
        logger.info(f"Average score: {sum(scores)/len(scores):.2f}/10")
        logger.info(f"Min score: {min(scores):.2f}/10")
        logger.info(f"Max score: {max(scores):.2f}/10")
        logger.info(f"")
        logger.info(f"Score distribution:")
        logger.info(f"  • Excellent (8.3+): {len([s for s in scores if s >= 8.3])} listings")
        logger.info(f"  • Very Good (7.5-8.3): {len([s for s in scores if 7.5 <= s < 8.3])} listings")
        logger.info(f"  • Good (6.5-7.5): {len([s for s in scores if 6.5 <= s < 7.5])} listings")
        logger.info(f"  • Average (5.5-6.5): {len([s for s in scores if 5.5 <= s < 6.5])} listings")
        logger.info(f"  • Below (< 5.5): {len([s for s in scores if s < 5.5])} listings")
        logger.info(f"")
        logger.info(f"{'='*80}")
        logger.info(f"✅ Validation complete! Review the high-scoring deals above.")
        logger.info(f"{'='*80}")


def test_specific_listing(site_ad_id: str):
    """
    Test scoring for a specific listing by site_ad_id
    """
    engine = create_engine(settings.DATABASE_SYNC_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    sql = """
        SELECT 
            site_ad_id,
            url,
            parsed_data->>'brand' as brand,
            parsed_data->>'model' as model,
            CAST(parsed_data->>'year' AS INTEGER) as year,
            CAST(parsed_data->>'price' AS INTEGER) as price,
            CAST(parsed_data->>'mileage_km' AS INTEGER) as mileage_km,
            parsed_data->>'fuel' as fuel,
            parsed_data->>'gearbox' as gearbox,
            first_seen_at,
            updated_at
        FROM listings_raw
        WHERE site_ad_id = :site_ad_id
    """
    
    result = session.execute(text(sql), {'site_ad_id': site_ad_id})
    listing = result.fetchone()
    
    if not listing:
        logger.error(f"❌ Listing {site_ad_id} not found")
        session.close()
        return
    
    site_ad_id, url, brand, model, year, price, mileage_km, fuel, gearbox, first_seen, updated = listing
    
    logger.info(f"Testing specific listing: {brand} {model} ({year})")
    
    score_result = _evaluate_listing_enhanced(
        session,
        site_ad_id,
        brand, model, year, price, mileage_km, fuel, gearbox,
        first_seen, updated
    )
    
    if score_result:
        logger.info(f"Score: {score_result['score']:.2f}/10")
        logger.info(f"Reasons: {score_result['reasons']}")
    else:
        logger.error(f"Could not evaluate")
    
    session.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate CarScout scoring algorithm')
    parser.add_argument('--limit', type=int, default=20, help='Number of listings to sample (default: 20)')
    parser.add_argument('--listing', type=str, help='Test specific listing by site_ad_id')
    
    args = parser.parse_args()
    
    if args.listing:
        test_specific_listing(args.listing)
    else:
        sample_and_validate(args.limit)
