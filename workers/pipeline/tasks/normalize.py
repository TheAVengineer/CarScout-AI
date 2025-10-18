"""
Normalize task - Standardize and map fields
"""
from workers.pipeline.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def normalize_listing(self, listing_id: str):
    """
    Normalize listing fields
    
    Args:
        listing_id: UUID of the listing
    """
    # TODO: Implement normalization logic
    # 1. Map brand/model using brand_models table
    # 2. Standardize fuel, gearbox, body types
    # 3. Convert price to BGN
    # 4. Clean numeric fields (mileage, year)
    # 5. Update listings_normalized
    # 6. Trigger dedupe task
    
    return {"status": "normalized", "listing_id": listing_id}
