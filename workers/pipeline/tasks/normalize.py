"""
Normalize task - Standardize and map fields
"""
import hashlib
from uuid import UUID

from workers.pipeline.celery_app import celery_app
from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw, ListingNormalized, Seller
from libs.domain.normalization import BrandModelNormalizer, FieldNormalizer
from workers.pipeline.tasks.dedupe import deduplicate_listing


@celery_app.task(bind=True, max_retries=3)
def normalize_listing(self, listing_id: str):
    """
    Normalize listing fields
    
    Args:
        listing_id: UUID of the listing
    """
    session = get_sync_session()
    normalizer = BrandModelNormalizer()
    
    try:
        # Get raw listing
        raw_listing = session.query(ListingRaw).filter_by(id=UUID(listing_id)).first()
        if not raw_listing:
            return {"status": "error", "message": "Raw listing not found"}
        
        # Check if normalized version exists
        normalized = session.query(ListingNormalized).filter_by(raw_id=raw_listing.id).first()
        
        if not normalized:
            return {"status": "error", "message": "Normalized listing not found (parse task must run first)"}
        
        # Get brand/model from the already-parsed normalized listing
        brand_raw = normalized.brand_id or "Unknown"
        model_raw = normalized.model_id or "Unknown"
        
        # Normalize brand/model using the normalizer
        brand_id, model_id = normalizer.normalize(brand_raw, model_raw)
        
        # Normalize other fields from the existing normalized listing
        fuel = FieldNormalizer.normalize_fuel(normalized.fuel) if normalized.fuel else None
        gearbox = FieldNormalizer.normalize_gearbox(normalized.gearbox) if normalized.gearbox else None
        body = FieldNormalizer.normalize_body(normalized.body) if normalized.body else None
        mileage_km = FieldNormalizer.normalize_mileage(normalized.mileage_km) if normalized.mileage_km else None
        year = FieldNormalizer.normalize_year(normalized.year) if normalized.year else None
        
        # Price is already in BGN from parse task
        price_bgn = normalized.price_bgn
        
        # Handle seller (if phone hash available)
        phone_hash = None  # TODO: Extract from parsed data when phone parsing is implemented
        seller_id = None
        if phone_hash:
            seller = session.query(Seller).filter_by(phone_hash=phone_hash).first()
            if not seller:
                seller = Seller(phone_hash=phone_hash)
                session.add(seller)
                session.flush()
            seller_id = seller.id
        
        # Generate description hash if description exists
        description_hash = None
        if normalized.description:
            description_hash = hashlib.sha256(normalized.description.encode()).hexdigest()
        
        # Update the normalized listing with standardized values
        normalized.brand_id = brand_id
        normalized.model_id = model_id
        normalized.fuel = fuel
        normalized.gearbox = gearbox
        normalized.body = body
        normalized.mileage_km = mileage_km
        normalized.year = year
        normalized.price_bgn = price_bgn
        if seller_id:
            normalized.seller_id = seller_id
        if description_hash:
            normalized.description_hash = description_hash
        normalized.listing_version += 1
        
        session.commit()
        
        # Get the normalized listing ID (not the raw ID!)
        session.refresh(normalized)
        normalized_id = str(normalized.id)
        
        # Trigger next task (deduplication) with the NORMALIZED listing ID
        deduplicate_listing.delay(normalized_id)
        
        return {
            "status": "normalized",
            "listing_id": listing_id,
            "brand": brand_id,
            "model": model_id,
        }
        
    except Exception as e:
        session.rollback()
        raise self.retry(exc=e, countdown=60)
    finally:
        session.close()
