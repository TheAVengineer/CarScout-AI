#!/usr/bin/env python3
"""
Test OpenAI API integration with GPT-4o mini
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configs.settings import settings

def test_openai_config():
    print("🤖 Testing OpenAI Configuration")
    print("=" * 60)
    print()
    
    # Check if API key is configured
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "YOUR_OPENAI_KEY_HERE":
        print("❌ OpenAI API key not configured")
        return 1
    
    print(f"✅ OpenAI API Key: {settings.OPENAI_API_KEY[:20]}...{settings.OPENAI_API_KEY[-10:]}")
    print(f"✅ Model: {settings.OPENAI_MODEL}")
    print()
    
    # Test OpenAI connection
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        print("🔄 Testing API connection with a simple request...")
        print()
        
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful car listing analyzer."},
                {"role": "user", "content": "What are the top 3 things to check when buying a used car? Answer in one sentence."}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content
        
        print("✅ OpenAI API is working!")
        print()
        print(f"Test Question: What are the top 3 things to check when buying a used car?")
        print(f"Response: {answer}")
        print()
        print(f"Model used: {response.model}")
        print(f"Tokens used: {response.usage.total_tokens} (prompt: {response.usage.prompt_tokens}, completion: {response.usage.completion_tokens})")
        print()
        
        print("=" * 60)
        print("✅ OpenAI integration test PASSED")
        print()
        print("You can now use GPT-4o mini for:")
        print("  - Risk evaluation of car listings")
        print("  - Generating listing summaries")
        print("  - Detecting scam patterns")
        print("  - Analyzing seller descriptions")
        
        return 0
        
    except ImportError:
        print("❌ OpenAI package not installed")
        print("Install with: pip install openai")
        return 1
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_openai_config())
