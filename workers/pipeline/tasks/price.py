"""
Pricing task - Estimate market price using ML model
"""
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy import and_, func

from workers.pipeline.celery_app import celery_app
from libs.domain.database import get_sync_session
from libs.domain.models import ListingNormalized, CompCache, PriceHistory
from workers.pipeline.tasks.ai import classify_risk

logger = logging.getLogger(__name__)


class PricingModel:
    """ML-based pricing model using comparable vehicles"""
    
    def __init__(self, session):
        self.session = session
    
    def get_comparables(
        self,
        brand: str,
        model: str,
        year: int,
        mileage: int,
        fuel: str = None,
        gearbox: str = None,
        max_age: int = 180,  # days
        limit: int = 50
    ) -> List[ListingNormalized]:
        """Find comparable vehicles"""
        
        # Calculate date threshold
        date_threshold = datetime.now(timezone.utc) - timedelta(days=max_age)
        
        # Build query
        query = self.session.query(ListingNormalized).filter(
            and_(
                ListingNormalized.brand_id == brand,
                ListingNormalized.model_id == model,
                ListingNormalized.is_duplicate == False,
                ListingNormalized.price_bgn.isnot(None),
                ListingNormalized.price_bgn > 500,  # Minimum reasonable price
                ListingNormalized.created_at >= date_threshold,
            )
        )
        
        # Add year filter (± 2 years)
        if year:
            query = query.filter(
                ListingNormalized.year.between(year - 2, year + 2)
            )
        
        # Add mileage filter (± 30%)
        if mileage:
            query = query.filter(
                ListingNormalized.mileage_km.between(
                    int(mileage * 0.7),
                    int(mileage * 1.3)
                )
            )
        
        # Add fuel type filter
        if fuel:
            query = query.filter(ListingNormalized.fuel == fuel)
        
        # Add gearbox filter
        if gearbox:
            query = query.filter(ListingNormalized.gearbox == gearbox)
        
        # Order by relevance (closest year and mileage)
        comparables = query.limit(limit).all()
        
        return comparables
    
    def calculate_statistics(self, prices: List[float]) -> Dict[str, float]:
        """Calculate price statistics"""
        if not prices:
            return None
        
        import numpy as np
        
        prices_array = np.array(prices)
        
        return {
            'p10': float(np.percentile(prices_array, 10)),
            'p25': float(np.percentile(prices_array, 25)),
            'p50': float(np.percentile(prices_array, 50)),  # Median
            'p75': float(np.percentile(prices_array, 75)),
            'p90': float(np.percentile(prices_array, 90)),
            'mean': float(np.mean(prices_array)),
            'std': float(np.std(prices_array)),
            'min': float(np.min(prices_array)),
            'max': float(np.max(prices_array)),
            'count': len(prices),
        }
    
    def estimate_price(self, listing: ListingNormalized) -> Optional[Dict[str, Any]]:
        """Estimate price for listing"""
        
        if not listing.brand_id or not listing.model_id:
            logger.warning(f"Listing {listing.id} missing brand/model")
            return None
        
        # Find comparable vehicles
        comparables = self.get_comparables(
            brand=listing.brand_id,
            model=listing.model_id,
            year=listing.year,
            mileage=listing.mileage_km,
            fuel=listing.fuel,
            gearbox=listing.gearbox,
        )
        
        if len(comparables) < 3:
            logger.warning(f"Not enough comparables for {listing.brand_id} {listing.model_id} ({len(comparables)} found)")
            # Try with relaxed filters
            comparables = self.get_comparables(
                brand=listing.brand_id,
                model=listing.model_id,
                year=listing.year,
                mileage=listing.mileage_km,
                max_age=365,  # 1 year
                limit=100
            )
        
        if len(comparables) < 3:
            logger.warning(f"Still not enough comparables ({len(comparables)} found)")
            return None
        
        # Extract prices and convert Decimal to float for NumPy
        prices = [float(comp.price_bgn) for comp in comparables if comp.price_bgn]
        
        if len(prices) < 3:
            return None
        
        # Calculate statistics
        stats = self.calculate_statistics(prices)
        
        # Use median as predicted price
        predicted_price = stats['p50']
        
        # Calculate discount percentage (convert Decimal to float)
        discount_pct = 0.0
        if listing.price_bgn and predicted_price > 0:
            listing_price = float(listing.price_bgn)
            discount_pct = ((predicted_price - listing_price) / predicted_price) * 100
        
        # Calculate confidence based on sample size and variance
        # More comparables and lower variance = higher confidence
        confidence = min(1.0, (len(prices) / 30.0))  # Max at 30 comparables
        if stats['std'] > 0:
            cv = stats['std'] / stats['mean']  # Coefficient of variation
            confidence *= max(0.5, 1.0 - cv)  # Penalize high variance
        
        return {
            'predicted_price_bgn': predicted_price,
            'price_p10': stats['p10'],
            'price_p50': stats['p50'],
            'price_p90': stats['p90'],
            'discount_pct': discount_pct,
            'comparable_count': len(prices),
            'confidence': confidence,
            'comparable_ids': [comp.id for comp in comparables[:10]],  # Store top 10
        }


@celery_app.task(bind=True, max_retries=3)
def estimate_price(self, listing_id: str):
    """Estimate market price for listing"""
    session = get_sync_session()
    
    try:
        # Get listing
        listing = session.query(ListingNormalized).filter_by(id=UUID(listing_id)).first()
        
        if not listing:
            logger.error(f"Listing {listing_id} not found")
            return
        
        # Initialize pricing model
        model = PricingModel(session)
        
        # Estimate price
        result = model.estimate_price(listing)
        
        if not result:
            logger.warning(f"Could not estimate price for {listing_id} (not enough data)")
            # Continue pipeline anyway
            classify_risk.delay(listing_id)
            return
        
        # Update listing
        listing.predicted_price_bgn = result['predicted_price_bgn']
        listing.discount_pct = result['discount_pct']
        
        # Create/update comp cache
        comp_cache = session.query(CompCache).filter_by(listing_id=listing.id).first()
        
        if comp_cache:
            # Update existing
            comp_cache.predicted_price_bgn = result['predicted_price_bgn']
            comp_cache.discount_pct = result['discount_pct']
            comp_cache.p10 = result['price_p10']
            comp_cache.p50 = result['price_p50']
            comp_cache.p90 = result['price_p90']
            comp_cache.sample_size = result['comparable_count']
            comp_cache.computed_at = datetime.now(timezone.utc)
            comp_cache.model_version = 'comparable_v1'
        else:
            # Create new
            comp_cache = CompCache(
                listing_id=listing.id,
                predicted_price_bgn=result['predicted_price_bgn'],
                discount_pct=result['discount_pct'],
                p10=result['price_p10'],
                p50=result['price_p50'],
                p90=result['price_p90'],
                sample_size=result['comparable_count'],
                model_version='comparable_v1',
            )
            session.add(comp_cache)
        
        # Track price history
        price_history = PriceHistory(
            listing_id=listing.id,
            price_bgn=listing.price_bgn,
            seen_at=datetime.now(timezone.utc),
        )
        session.add(price_history)
        
        session.commit()
        
        logger.info(
            f"Estimated price for {listing_id}: "
            f"predicted={result['predicted_price_bgn']:.0f} BGN, "
            f"actual={listing.price_bgn:.0f} BGN, "
            f"discount={result['discount_pct']:.1f}%, "
            f"comparables={result['comparable_count']}, "
            f"confidence={result['confidence']:.2f}"
        )
        
        # Trigger next task (AI evaluation)
        classify_risk.delay(listing_id)
        
        return {
            "status": "priced",
            "listing_id": listing_id,
            "predicted_price": result['predicted_price_bgn'],
            "discount_pct": result['discount_pct'],
            "confidence": result['confidence'],
        }
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error estimating price for {listing_id}: {e}", exc_info=True)
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
    
    finally:
        session.close()
