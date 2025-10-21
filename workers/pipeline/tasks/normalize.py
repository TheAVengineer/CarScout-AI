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
        
        # Get parsed data (would come from parsing step in real implementation)
        # For now, assume it's in raw_listing metadata
        
        # Normalize brand/model
        brand_raw = "BMW"  # TODO: Get from parsed data
        model_raw = "X5"   # TODO: Get from parsed data
        brand_id, model_id = normalizer.normalize(brand_raw, model_raw)
        
        # Normalize other fields
        fuel = FieldNormalizer.normalize_fuel("diesel")  # TODO: From parsed
        gearbox = FieldNormalizer.normalize_gearbox("automatic")  # TODO: From parsed
        body = FieldNormalizer.normalize_body("SUV")  # TODO: From parsed
        mileage_km = FieldNormalizer.normalize_mileage(120000)  # TODO: From parsed
        year = FieldNormalizer.normalize_year(2018)  # TODO: From parsed
        price_bgn = FieldNormalizer.convert_price_to_bgn(30000, 'EUR')  # TODO: From parsed
        
        # Handle seller
        phone_hash = "sample_hash"  # TODO: From parsed
        seller = session.query(Seller).filter_by(phone_hash=phone_hash).first()
        if not seller:
            seller = Seller(phone_hash=phone_hash)
            session.add(seller)
            session.flush()
        
        # Generate description hash
        description = "Sample description"  # TODO: From parsed
        description_hash = hashlib.sha256(description.encode()).hexdigest()
        
        if normalized:
            # Update existing
            normalized.brand_id = brand_id
            normalized.model_id = model_id
            normalized.fuel = fuel
            normalized.gearbox = gearbox
            normalized.body = body
            normalized.mileage_km = mileage_km
            normalized.year = year
            normalized.price_bgn = price_bgn
            normalized.seller_id = seller.id
            normalized.description_hash = description_hash
            normalized.listing_version += 1
        else:
            # Create new
            normalized = ListingNormalized(
                raw_id=raw_listing.id,
                brand_id=brand_id,
                model_id=model_id,
                fuel=fuel,
                gearbox=gearbox,
                body=body,
                mileage_km=mileage_km,
                year=year,
                price_bgn=price_bgn,
                seller_id=seller.id,
                description_hash=description_hash,
                listing_version=1,
            )
            session.add(normalized)
        
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
