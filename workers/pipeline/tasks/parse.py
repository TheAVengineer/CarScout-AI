"""
Parse task - Extract fields from raw HTML
"""
from workers.pipeline.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def parse_listing(self, listing_id: str, raw_html_path: str, source_id: str):
    """
    Parse raw HTML and extract structured fields
    
    Args:
        listing_id: UUID of the listing
        raw_html_path: S3 path to raw HTML
        source_id: Source identifier
    """
    # TODO: Implement parsing logic per source
    # 1. Download HTML from S3
    # 2. Parse with appropriate parser (Scrapy selectors, lxml)
    # 3. Extract: brand, model, year, mileage, price, etc.
    # 4. Save to listings_normalized
    # 5. Trigger normalize task
    
    return {"status": "parsed", "listing_id": listing_id}
