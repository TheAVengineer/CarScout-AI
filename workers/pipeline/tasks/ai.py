"""
AI evaluation task - Risk classification and LLM summary
"""
from workers.pipeline.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def classify_risk(self, listing_id: str):
    """
    Classify risk using rules and optionally LLM
    
    Args:
        listing_id: UUID of the listing
    """
    # TODO: Implement risk classification
    # 1. Apply regex/keyword rules
    # 2. Generate flags JSONB
    # 3. Calculate rule_confidence
    # 4. Save to evaluations
    # 5. Trigger score task
    
    return {
        "status": "classified",
        "listing_id": listing_id,
        "risk_level": "low",
    }


@celery_app.task(bind=True, max_retries=3)
def llm_evaluate(self, listing_id: str):
    """
    Get LLM evaluation for uncertain cases
    
    Args:
        listing_id: UUID of the listing
    """
    # TODO: Implement LLM evaluation
    # 1. Check cache by description_hash
    # 2. If not cached, call OpenAI API
    # 3. Parse risk_level, reasons, confidence
    # 4. Update evaluations
    # 5. Trigger score task
    
    return {
        "status": "evaluated",
        "listing_id": listing_id,
        "llm_summary": "",
    }
