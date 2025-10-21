#!/usr/bin/env python3
"""
Synchronous pipeline test - runs all stages for one listing to see where it fails
"""
import sys
from uuid import UUID
from libs.domain.database import get_sync_session
from libs.domain.models import ListingNormalized, Score
from workers.pipeline.tasks.price import PriceEstimator
from workers.pipeline.tasks.ai import RiskClassifier, LLMEvaluator
from workers.pipeline.tasks.score import ScoreCalculator

def main():
    session = get_sync_session().__enter__()
    
    # Get a listing without a score
    listing = session.query(ListingNormalized).outerjoin(Score).filter(Score.id == None).first()
    
    if not listing:
        print("No listings without scores found!")
        return
    
    print(f"\n=== Testing Pipeline for Listing {listing.id} ===")
    print(f"Brand/Model: {listing.brand_id} / {listing.model_id}")
    print(f"Year: {listing.year}, Mileage: {listing.mileage_km} km")
    print(f"Price: {listing.price_bgn} BGN")
    print(f"Fuel: {listing.fuel}, Gearbox: {listing.gearbox}")
    
    # Stage 1: Price Estimation
    print("\n--- Stage 1: Price Estimation ---")
    estimator = PriceEstimator()
    try:
        price_data = estimator.estimate(listing)
        print(f"✅ Price estimated: {price_data}")
    except Exception as e:
        print(f"❌ Price estimation failed: {e}")
        price_data = None
    
    # Stage 2: Risk Classification
    print("\n--- Stage 2: Risk Classification ---")
    classifier = RiskClassifier()
    try:
        risk_data = classifier.classify(listing)
        print(f"✅ Risk classified: {risk_data}")
    except Exception as e:
        print(f"❌ Risk classification failed: {e}")
        risk_data = None
    
    # Stage 3: LLM Evaluation
    print("\n--- Stage 3: LLM Evaluation ---")
    evaluator = LLMEvaluator()
    try:
        llm_data = evaluator.evaluate(listing)
        print(f"✅ LLM evaluated: {llm_data}")
    except Exception as e:
        print(f"❌ LLM evaluation failed: {e}")
        llm_data = None
    
    # Stage 4: Score Calculation
    print("\n--- Stage 4: Score Calculation ---")
    calculator = ScoreCalculator()
    try:
        score = calculator.calculate(listing, session)
        print(f"✅ Score calculated: {score.score} ({score.final_state})")
        print(f"   Reasons: {score.reasons}")
    except Exception as e:
        print(f"❌ Score calculation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
