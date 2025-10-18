"""
Scoring task - Calculate final score and approve/reject
"""
from workers.pipeline.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def calculate_score(self, listing_id: str):
    """
    Calculate final listing score
    
    Args:
        listing_id: UUID of the listing
    """
    # TODO: Implement scoring logic
    # 1. Load price advantage (from comps_cache)
    # 2. Load risk penalty (from evaluations)
    # 3. Calculate freshness bonus
    # 4. Apply business rules
    # 5. Compute final score (1-10)
    # 6. Determine state (approved/rejected)
    # 7. Save to scores
    # 8. If approved, trigger notify tasks
    
    return {
        "status": "scored",
        "listing_id": listing_id,
        "score": 0.0,
        "state": "draft",
    }


@celery_app.task(bind=True, max_retries=3)
def rescore_stale_listings(self):
    """
    Rescore listings that haven't been updated recently
    """
    # TODO: Find stale listings and rescore
    return {"status": "completed", "rescored_count": 0}
