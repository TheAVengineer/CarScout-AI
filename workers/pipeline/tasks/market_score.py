"""
Market-Aware Scoring Task
=========================

Uses intelligent scoring with:
- Database comparables
- Price bracket awareness
- Red flag detection
- Market context

This replaces both simple_score and the old complex pipeline.
"""
import logging
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from workers.pipeline.celery_app import celery_app
from libs.domain.database import get_sync_session
from libs.domain.models import ListingNormalized, Score
from libs.domain.market_aware_scoring import create_market_aware_engine
from workers.pipeline.tasks.notify import post_to_channel

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, name="market_aware_score")
def market_aware_score(self, listing_id: str):
    """
    Score listing with market-aware intelligence.
    
    This is the BEST scoring system:
    - Uses real comparables from database
    - Understands price brackets
    - Detects red flags (leasing, RHD, scams)
    - Context-aware scoring
    """
    session = get_sync_session()
    
    try:
        # Get listing
        listing = session.query(ListingNormalized).filter_by(id=UUID(listing_id)).first()
        
        if not listing:
            logger.error(f"Listing {listing_id} not found")
            return {'error': 'Listing not found'}
        
        # Basic validation
        if not listing.brand_id or not listing.model_id or not listing.price_bgn:
            logger.warning(f"Listing {listing_id} missing required fields")
            return {'error': 'Missing required fields'}
        
        # Create market-aware engine
        engine = create_market_aware_engine(session)
        
        # Rate the listing
        rating = engine.rate_listing(
            listing_id=listing_id,
            price_bgn=listing.price_bgn,
            year=listing.year or 0,
            mileage_km=listing.mileage_km,
            brand=listing.brand_id,
            model=listing.model_id,
            fuel_type=listing.fuel,  # Fixed: use 'fuel' not 'fuel_type'
            body_type=listing.body,  # Fixed: use 'body' not 'body_type'
            description=listing.description or '',
            title=listing.title or '',
            image_count=0,  # TODO: Get from raw listing
            created_at=listing.created_at,
            location=None,  # TODO: Extract from description
        )
        
        # Determine state
        if rating.get('blocked'):
            state = 'rejected'
            logger.info(
                f"🚫 Listing {listing_id[:8]} BLOCKED: {rating['block_reason']}\n"
                f"   {listing.brand_id} {listing.model_id} {listing.year} - {listing.price_bgn:,} BGN"
            )
        elif rating['should_post']:
            state = 'approved'
            logger.info(
                f"✅ Listing {listing_id[:8]} APPROVED → {rating['score']:.2f}/10\n"
                f"   {listing.brand_id} {listing.model_id} {listing.year} - {listing.price_bgn:,} BGN\n"
                f"   Market: {rating['market_context'].get('discount_pct', 0):.1f}% below median "
                f"({rating['market_context'].get('comparable_count', 0)} comps)\n"
                f"   Reasons: {', '.join(rating['reasons'][:3])}"
            )
        elif rating['score'] >= 6.0:
            state = 'draft'
            logger.info(
                f"📝 Listing {listing_id[:8]} DRAFT → {rating['score']:.2f}/10 (threshold: 7.5)\n"
                f"   {listing.brand_id} {listing.model_id} {listing.year} - {listing.price_bgn:,} BGN\n"
                f"   Discount: {rating['market_context'].get('discount_pct', 0):.1f}%"
            )
        else:
            state = 'rejected'
            logger.debug(
                f"❌ Listing {listing_id[:8]} rejected → {rating['score']:.2f}/10"
            )
        
        # Save to database
        existing_score = session.query(Score).filter_by(listing_id=listing.id).first()
        
        # Prepare reasons + red flags
        all_reasons = rating.get('reasons', []) + rating.get('red_flags', [])
        
        if existing_score:
            # Update
            existing_score.score = rating['score']
            existing_score.final_state = state
            existing_score.reasons = all_reasons
            existing_score.scored_at = datetime.now(timezone.utc)
            # Store market context in available fields
            existing_score.risk_penalty = -1 * len(rating['red_flags'])  # Use as flag counter
            existing_score.liquidity = rating['market_context'].get('comparable_count', 0)
            existing_score.freshness_bonus = rating['market_context'].get('discount_pct', 0)  # Store discount % here
        else:
            # Create new
            score_record = Score(
                listing_id=listing.id,
                score=rating['score'],
                risk_penalty=-1 * len(rating['red_flags']),
                freshness_bonus=rating['market_context'].get('discount_pct', 0),  # Store discount % here
                liquidity=rating['market_context'].get('comparable_count', 0),
                final_state=state,
                reasons=all_reasons,
            )
            session.add(score_record)
        
        session.commit()
        
        # Post to Telegram if approved
        if rating['should_post']:
            logger.info(f"📱 Posting to Telegram...")
            post_to_channel.delay(listing_id)
        
        return {
            'listing_id': listing_id,
            'score': rating['score'],
            'state': state,
            'should_post': rating['should_post'],
            'discount_pct': rating['market_context'].get('discount_pct', 0),
            'comparable_count': rating['market_context'].get('comparable_count', 0),
            'red_flags': rating.get('red_flags', []),
            'blocked': rating.get('blocked', False),
        }
        
    except Exception as e:
        logger.error(f"Error scoring listing {listing_id}: {e}", exc_info=True)
        session.rollback()
        raise
    finally:
        session.close()


@celery_app.task(bind=True, name="score_fresh_market_aware")
def score_fresh_market_aware(self, hours: int = 48, limit: int = 1000):
    """
    Score fresh listings with market-aware system.
    
    This finds new listings and scores them intelligently,
    using database comparables and red flag detection.
    
    Args:
        hours: Look back this many hours for new listings
        limit: Maximum listings to process in one batch
    """
    session = get_sync_session()
    
    try:
        from sqlalchemy import text
        from datetime import timedelta
        
        # Get unscored listings from last X hours
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        query = text('''
            SELECT ln.id
            FROM listings_normalized ln
            LEFT JOIN scores s ON s.listing_id = ln.id
            WHERE ln.created_at >= :cutoff
            AND ln.brand_id IS NOT NULL
            AND ln.model_id IS NOT NULL
            AND ln.price_bgn IS NOT NULL
            AND ln.price_bgn BETWEEN 5000 AND 150000
            AND ln.year >= 2010
            AND s.id IS NULL
            ORDER BY ln.created_at DESC
            LIMIT :limit
        ''')
        
        result = session.execute(query, {'cutoff': cutoff, 'limit': limit})
        listing_ids = [str(row[0]) for row in result]
        
        logger.info(
            f"🎯 Found {len(listing_ids)} new listings from last {hours} hours\n"
            f"   Scoring with market-aware system..."
        )
        
        # Queue scoring tasks
        for lid in listing_ids:
            market_aware_score.delay(lid)
        
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
