"""
Scoring task - Calculate final score and approve/reject
"""
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta

from workers.pipeline.celery_app import celery_app
from libs.domain.database import get_sync_session
from libs.domain.models import ListingNormalized, Score, Evaluation, CompCache
from libs.domain.scoring import ScoringEngine
from workers.pipeline.tasks.notify import post_to_channel

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def calculate_score(self, listing_id: str):
    """Calculate final listing score and determine approval"""
    session = get_sync_session()
    
    try:
        # Get listing
        listing = session.query(ListingNormalized).filter_by(id=UUID(listing_id)).first()
        
        if not listing:
            logger.error(f"Listing {listing_id} not found")
            return
        
        # Get comp cache (pricing data)
        comp_cache = session.query(CompCache).filter_by(listing_id=listing.id).first()
        
        # Get evaluation (risk data)
        evaluation = session.query(Evaluation).filter_by(listing_id=listing.id).first()
        
        # Initialize scoring engine
        engine = ScoringEngine()
        
        # Prepare inputs
        discount_pct = comp_cache.discount_pct if comp_cache and comp_cache.discount_pct else 0.0
        risk_level = evaluation.risk_level if evaluation else 'unknown'
        
        # Calculate listing age (ensure both datetimes are timezone-aware)
        now_utc = datetime.now(timezone.utc)
        created_at = listing.created_at if listing.created_at.tzinfo else listing.created_at.replace(tzinfo=timezone.utc)
        age_hours = (now_utc - created_at).total_seconds() / 3600
        
        # Additional context for scoring
        comparable_count = comp_cache.sample_size if comp_cache else 0
        price_confidence = 0.5 if comp_cache else 0.0  # Default confidence
        
        # Calculate score using ScoringEngine
        score_result = engine.calculate_score(
            discount_pct=discount_pct,
            comp_sample_size=comparable_count,
            comp_confidence=price_confidence,
            risk_level=risk_level,
            freshness_hours=age_hours,
        )
        
        # Determine state based on scoring engine's approval decision
        if score_result['is_approved']:
            state = 'approved'
        elif score_result['score'] < 3.0 or risk_level == 'red':
            state = 'rejected'
        else:
            state = 'draft'
        
        # Create or update score
        existing_score = session.query(Score).filter_by(listing_id=listing.id).first()
        
        if existing_score:
            # Update existing
            existing_score.score = score_result['score']
            existing_score.risk_penalty = score_result['risk_penalty']
            existing_score.freshness_bonus = score_result['freshness_bonus']
            existing_score.liquidity = score_result.get('liquidity_bonus', 0.0)
            existing_score.final_state = state
            existing_score.reasons = score_result.get('reasons', [])
            existing_score.scored_at = datetime.now(timezone.utc)
            score_obj = existing_score
        else:
            # Create new
            score_obj = Score(
                listing_id=listing.id,
                score=score_result['score'],
                risk_penalty=score_result['risk_penalty'],
                freshness_bonus=score_result['freshness_bonus'],
                liquidity=score_result.get('liquidity_bonus', 0.0),
                final_state=state,
                reasons=score_result.get('reasons', []),
            )
            session.add(score_obj)
        
        session.commit()
        
        logger.info(
            f"Scored listing {listing_id}: "
            f"score={score_result['score']:.2f}, "
            f"state={state}, "
            f"price={score_result['price_score']:.2f}, "
            f"risk={score_result['risk_penalty']:.2f}, "
            f"fresh={score_result['freshness_bonus']:.2f}"
        )
        
        # If approved, trigger notification
        if state == 'approved':
            logger.info(f"Listing {listing_id} approved, triggering notification")
            post_to_channel.delay(listing_id)
        
        return {
            "status": "scored",
            "listing_id": listing_id,
            "score": score_result['score'],
            "state": state,
            "breakdown": score_result,
        }
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error calculating score for {listing_id}: {e}", exc_info=True)
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
    
    finally:
        session.close()


@celery_app.task(bind=True, max_retries=3)
def rescore_stale_listings(self):
    """Rescore listings that haven't been updated recently"""
    session = get_sync_session()
    
    try:
        # Find listings scored more than 24 hours ago that are still relevant
        threshold = datetime.now(timezone.utc) - timedelta(hours=24)
        listing_age_threshold = datetime.now(timezone.utc) - timedelta(days=7)
        
        stale_scores = session.query(Score).join(ListingNormalized).filter(
            Score.updated_at < threshold,
            Score.final_state == 'approved',
            ListingNormalized.created_at >= listing_age_threshold,
            ListingNormalized.is_duplicate == False,
        ).limit(100).all()
        
        rescored_count = 0
        
        for score in stale_scores:
            try:
                calculate_score.delay(str(score.listing_id))
                rescored_count += 1
            except Exception as e:
                logger.error(f"Failed to rescore {score.listing_id}: {e}")
        
        logger.info(f"Queued {rescored_count} listings for rescoring")
        
        return {
            "status": "completed",
            "rescored_count": rescored_count
        }
        
    except Exception as e:
        logger.error(f"Error in rescore_stale_listings: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=300)
    
    finally:
        session.close()
