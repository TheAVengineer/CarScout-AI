"""
AI evaluation task - Risk classification and LLM summary
"""
from uuid import UUID

from workers.pipeline.celery_app import celery_app
from libs.domain.database import get_sync_session
from libs.domain.models import ListingNormalized, Evaluation, CompCache
from libs.ml.risk_evaluation import RiskClassifier, LLMEvaluator


@celery_app.task(bind=True, max_retries=3)
def classify_risk(self, listing_id: str):
    """
    Classify risk using rules and optionally LLM
    
    Args:
        listing_id: UUID of the listing
    """
    session = get_sync_session()
    classifier = RiskClassifier()
    
    try:
        # Get listing
        listing = session.query(ListingNormalized).filter_by(id=UUID(listing_id)).first()
        if not listing:
            return {"status": "error", "message": "Listing not found"}
        
        # Run rule-based classification
        result = classifier.classify(
            title=listing.title or "",
            description=listing.description or ""
        )
        
        # Create or update evaluation
        evaluation = session.query(Evaluation).filter_by(listing_id=listing.id).first()
        if not evaluation:
            evaluation = Evaluation(listing_id=listing.id)
            session.add(evaluation)
        
        evaluation.flags = result['flags']
        evaluation.risk_level = result['risk_level']
        evaluation.rule_confidence = result['rule_confidence']
        evaluation.model_versions = {'rule_classifier': 'v1'}
        
        session.commit()
        
        # Trigger LLM if needed
        if result['needs_llm']:
            llm_evaluate.delay(listing_id)
        else:
            # Trigger scoring directly
            from workers.pipeline.tasks.score import calculate_score
            calculate_score.delay(listing_id)
        
        return {
            "status": "classified",
            "listing_id": listing_id,
            "risk_level": result['risk_level'],
            "needs_llm": result['needs_llm'],
        }
        
    except Exception as e:
        session.rollback()
        raise self.retry(exc=e, countdown=60)
    finally:
        session.close()


@celery_app.task(bind=True, max_retries=3)
def llm_evaluate(self, listing_id: str):
    """
    Get LLM evaluation for uncertain cases
    
    Args:
        listing_id: UUID of the listing
    """
    session = get_sync_session()
    evaluator = LLMEvaluator()
    
    try:
        # Get listing and existing evaluation
        listing = session.query(ListingNormalized).filter_by(id=UUID(listing_id)).first()
        if not listing:
            return {"status": "error", "message": "Listing not found"}
        
        evaluation = session.query(Evaluation).filter_by(listing_id=listing.id).first()
        if not evaluation:
            return {"status": "error", "message": "Evaluation not found"}
        
        # Get pricing data
        comp_cache = session.query(CompCache).filter_by(listing_id=listing.id).first()
        if not comp_cache:
            predicted_price = listing.price_bgn or 0
            discount_pct = 0.0
        else:
            predicted_price = float(comp_cache.predicted_price_bgn or 0)
            discount_pct = comp_cache.discount_pct or 0.0
        
        # Run LLM evaluation
        result = evaluator.evaluate(
            title=listing.title or "",
            description=listing.description or "",
            price_bgn=float(listing.price_bgn or 0),
            predicted_price_bgn=predicted_price,
            discount_pct=discount_pct,
            rule_flags=evaluation.flags or {},
        )
        
        # Update evaluation
        evaluation.llm_summary = result.get('summary', '')
        evaluation.llm_confidence = result.get('llm_confidence', 0.5)
        
        # Override risk level if LLM has higher confidence
        if result.get('llm_confidence', 0) > (evaluation.rule_confidence or 0):
            evaluation.risk_level = result.get('risk_level', 'medium')
        
        evaluation.model_versions = evaluation.model_versions or {}
        evaluation.model_versions['llm'] = result.get('model_version', '')
        
        session.commit()
        
        # Trigger scoring
        from workers.pipeline.tasks.score import calculate_score
        calculate_score.delay(listing_id)
        
        return {
            "status": "evaluated",
            "listing_id": listing_id,
            "llm_summary": result.get('summary', ''),
            "risk_level": evaluation.risk_level,
        }
        
    except Exception as e:
        session.rollback()
        raise self.retry(exc=e, countdown=60)
    finally:
        session.close()
