"""
Simple Scoring Task for New Listings
=====================================

This replaces the complex ML-based scoring with a transparent,
rule-based system that's easy to understand and tune.

Focus: New listings (last 48 hours) only.
No complex ML models, no comparable matching, just clear rules.
"""
import logging
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from workers.pipeline.celery_app import celery_app
from libs.domain.database import get_sync_session
from libs.domain.models import ListingNormalized, Score
from libs.domain.simple_scoring import SimpleRatingEngine
from workers.pipeline.tasks.notify import post_to_channel

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, name="simple_score_listing")
def simple_score_listing(self, listing_id: str):
    """
    Score a listing with simple, transparent rules.
    If score >= threshold, post to Telegram.
    
    This is MUCH simpler than the old system:
    - No ML models
    - No comparable matching
    - No risk classification
    - Just clear, understandable rules
    """
    session = get_sync_session()
    
    try:
        # Get listing
        listing = session.query(ListingNormalized).filter_by(id=UUID(listing_id)).first()
        
        if not listing:
            logger.error(f"Listing {listing_id} not found")
            return {'error': 'Listing not found'}
        
        # Initialize simple rating engine
        engine = SimpleRatingEngine(
            posting_threshold=8.0,  # Only excellent deals (8.0+)
            min_price=5000,         # Skip very cheap cars
            max_price=100000,       # Skip luxury cars
            min_year=2015,          # Skip older cars
            max_mileage=150000,     # Skip high-mileage
        )
        
        # Calculate score
        rating = engine.rate_listing(
            price_bgn=listing.price_bgn or 0,
            year=listing.year or 0,
            mileage_km=listing.mileage_km,
            brand=listing.brand_id or '',
            model=listing.model_id or '',
            fuel_type=listing.fuel_type,
            description_length=len(listing.description or ''),
            image_count=len(listing.image_urls) if listing.image_urls else 0,
            created_at=listing.created_at,
        )
        
        # Determine state
        if rating['should_post']:
            state = 'approved'
        elif rating['score'] >= 7.0:
            state = 'draft'  # Good but not excellent
        else:
            state = 'rejected'
        
        # Log the rating
        logger.info(
            f"📊 Listing {listing_id[:8]} scored {rating['score']:.2f} → {state.upper()}\n"
            f"   Brand: {listing.brand_id} {listing.model_id}\n"
            f"   Price: {listing.price_bgn:,} BGN | Year: {listing.year} | Mileage: {listing.mileage_km or 'N/A'}\n"
            f"   Components: Price={rating['components']['price_score']:.1f}, "
            f"Age={rating['components']['age_score']:.1f}, "
            f"Mileage={rating['components']['mileage_score']:.1f}, "
            f"Quality={rating['components']['quality_score']:.1f}, "
            f"Fresh={rating['components']['freshness_score']:.1f}\n"
            f"   Reasons: {', '.join(rating['reasons'])}\n"
            f"   Warnings: {', '.join(rating['warnings']) if rating['warnings'] else 'None'}"
        )
        
        # Save to database (reuse Score model)
        existing_score = session.query(Score).filter_by(listing_id=listing.id).first()
        
        if existing_score:
            # Update
            existing_score.score = rating['score']
            existing_score.final_state = state
            existing_score.reasons = rating['reasons'] + rating['warnings']
            existing_score.scored_at = datetime.now(timezone.utc)
        else:
            # Create new
            score_record = Score(
                listing_id=listing.id,
                score=rating['score'],
                price_score=rating['components']['price_score'],
                risk_penalty=0.0,  # Not used in simple system
                freshness_bonus=rating['components']['freshness_score'],
                liquidity=0.0,  # Not used in simple system
                final_state=state,
                reasons=rating['reasons'] + rating['warnings'],
            )
            session.add(score_record)
        
        session.commit()
        
        # Post to Telegram if approved
        if rating['should_post']:
            logger.info(f"✅ APPROVED! Posting to Telegram...")
            post_to_channel.delay(listing_id)
        
        return {
            'listing_id': listing_id,
            'score': rating['score'],
            'state': state,
            'should_post': rating['should_post'],
            'reasons': rating['reasons'],
            'warnings': rating['warnings'],
        }
        
    except Exception as e:
        logger.error(f"Error scoring listing {listing_id}: {e}", exc_info=True)
        session.rollback()
        raise
    finally:
        session.close()


@celery_app.task(bind=True, name="score_fresh_listings")
def score_fresh_listings(self, hours: int = 48):
    """
    Score all new listings from the last X hours.
    
    This should run every 1-2 hours to catch new deals quickly.
    
    Args:
        hours: How far back to look for new listings (default: 48 hours)
    """
    session = get_sync_session()
    
    try:
        from sqlalchemy import text
        from datetime import timedelta
        
        # Get all unscored listings from last X hours
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        query = text('''
            SELECT ln.id
            FROM listings_normalized ln
            LEFT JOIN scores s ON s.listing_id = ln.id
            WHERE ln.created_at >= :cutoff
            AND ln.brand_id IS NOT NULL
            AND ln.model_id IS NOT NULL
            AND ln.price_bgn IS NOT NULL
            AND ln.price_bgn BETWEEN 5000 AND 100000
            AND ln.year >= 2015
            AND s.id IS NULL
            ORDER BY ln.created_at DESC
        ''')
        
        result = session.execute(query, {'cutoff': cutoff})
        listing_ids = [str(row[0]) for row in result]
        
        logger.info(f"🎯 Found {len(listing_ids)} new listings from last {hours} hours to score")
        
        # Queue scoring tasks
        for lid in listing_ids:
            simple_score_listing.delay(lid)
        
        return {
            'queued': len(listing_ids),
            'hours': hours,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Error queuing fresh listings: {e}", exc_info=True)
        raise
    finally:
        session.close()
