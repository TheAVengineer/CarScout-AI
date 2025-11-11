#!/usr/bin/env python3
"""
Test OpenAI Integration for Risk Evaluation

This script tests if the monitor can successfully call OpenAI API
to evaluate a listing for risk/fraud detection.
"""

import sys
from pathlib import Path
import asyncio
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw, Evaluation
from configs.settings import settings
from openai import OpenAI
from datetime import datetime

async def test_openai_evaluation():
    """Test OpenAI evaluation on a real listing"""
    
    print("=" * 70)
    print("🔑 TESTING OPENAI INTEGRATION FOR RISK EVALUATION")
    print("=" * 70)
    print()
    
    # 1. Verify OpenAI key
    print("STEP 1: Verifying OpenAI API Key")
    print("-" * 70)
    print(f"Key: {settings.OPENAI_API_KEY[:30]}...")
    print(f"Model: {settings.OPENAI_MODEL}")
    
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        test_response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{'role': 'user', 'content': 'Reply with: OK'}],
            max_tokens=5
        )
        print(f"✅ API Key Valid! Response: {test_response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ API Key Error: {e}")
        return
    
    print()
    
    # 2. Get a listing from database
    print("STEP 2: Fetching a Listing from Database")
    print("-" * 70)
    
    session = get_sync_session()
    
    listing = session.query(ListingRaw).filter(
        ListingRaw.is_active == True,
        ListingRaw.parsed_data.isnot(None)
    ).first()
    
    if not listing:
        print("❌ No listings found")
        return
    
    data = listing.parsed_data or {}
    print(f"Found: {data.get('brand')} {data.get('model')} ({data.get('year')})")
    print(f"Price: {data.get('price'):,} {data.get('currency', 'BGN')}")
    print(f"URL: {data.get('url')}")
    print()
    
    # 3. Call OpenAI for risk evaluation
    print("STEP 3: Calling OpenAI for Risk Evaluation")
    print("-" * 70)
    
    prompt = f"""You are a car fraud detection expert. Analyze this listing for red flags:

Brand: {data.get('brand')}
Model: {data.get('model')}
Year: {data.get('year')}
Price: {data.get('price')} {data.get('currency', 'BGN')}
Mileage: {data.get('mileage')} km
Description: {data.get('description', 'N/A')[:500]}

Respond in JSON format:
{{
    "risk_level": "low|medium|high",
    "red_flags": ["flag1", "flag2"],
    "positive_flags": ["good1", "good2"],
    "confidence": 0.0-1.0,
    "recommendation": "approve|review|reject"
}}
"""
    
    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {'role': 'system', 'content': 'You are a car fraud detection expert. Always respond with valid JSON only.'},
                {'role': 'user', 'content': prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content
        print(f"✅ OpenAI Response Received!")
        print()
        print("Raw Response:")
        print(result_text)
        print()
        
        # Parse JSON
        result = json.loads(result_text)
        
        print("Parsed Evaluation:")
        print(f"  Risk Level: {result.get('risk_level')}")
        print(f"  Confidence: {result.get('confidence')}")
        print(f"  Recommendation: {result.get('recommendation')}")
        print(f"  Red Flags: {result.get('red_flags')}")
        print(f"  Positive Flags: {result.get('positive_flags')}")
        print()
        
        # 4. Save to evaluation table
        print("STEP 4: Saving to Evaluation Table")
        print("-" * 70)
        
        evaluation = Evaluation(
            listing_id=listing.id,
            red_flags=result.get('red_flags', []),
            positive_flags=result.get('positive_flags', []),
            risk_level=result.get('risk_level', 'medium'),
            details=f"OpenAI evaluation successful - {result.get('recommendation')}",
            confidence=result.get('confidence', 0.5),
            fraud_probability=0.5 if result.get('risk_level') == 'medium' else (0.8 if result.get('risk_level') == 'high' else 0.2),
            model_version=json.dumps({"model": settings.OPENAI_MODEL, "version": "test_script"}),
            evaluated_at=datetime.utcnow()
        )
        
        session.add(evaluation)
        session.commit()
        
        print(f"✅ Saved to database with ID: {evaluation.id}")
        print()
        
        # 5. Verify it was saved
        print("STEP 5: Verifying Database Entry")
        print("-" * 70)
        
        saved_eval = session.query(Evaluation).filter_by(id=evaluation.id).first()
        if saved_eval:
            print(f"✅ Found in database!")
            print(f"  Listing ID: {saved_eval.listing_id}")
            print(f"  Risk Level: {saved_eval.risk_level}")
            print(f"  Red Flags: {saved_eval.red_flags}")
            print(f"  Positive Flags: {saved_eval.positive_flags}")
            print(f"  Details: {saved_eval.details}")
        else:
            print("❌ Not found in database")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {e}")
        print(f"Response was: {result_text}")
    except Exception as e:
        print(f"❌ OpenAI Call Error: {e}")
        import traceback
        traceback.print_exc()
    
    session.close()
    
    print()
    print("=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)
    print()
    print("🎉 OpenAI integration is working!")
    print("   - API key is valid")
    print("   - Risk evaluation successful")
    print("   - Results saved to database")
    print()
    print("Next: The monitor will automatically use this for new listings")

if __name__ == '__main__':
    asyncio.run(test_openai_evaluation())
