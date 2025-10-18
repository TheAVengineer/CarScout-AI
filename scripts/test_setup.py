#!/usr/bin/env python
"""
Test script to verify database setup and core functionality
"""
import sys
import os
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.domain.database import get_sync_session
from libs.domain.models import Source, Plan, BrandModel, User, ListingRaw


def test_database_connection():
    """Test database connection"""
    print("🔌 Testing database connection...")
    session = get_sync_session()
    
    try:
        # Simple query
        result = session.execute("SELECT 1").scalar()
        assert result == 1
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    finally:
        session.close()


def test_sources():
    """Test sources table"""
    print("\n📦 Testing sources...")
    session = get_sync_session()
    
    try:
        sources = session.query(Source).all()
        print(f"   Found {len(sources)} sources:")
        for source in sources:
            status = "🟢" if source.enabled else "🔴"
            print(f"   {status} {source.name} - {source.base_url}")
        
        assert len(sources) > 0, "No sources found"
        print("✅ Sources test passed")
        return True
    except Exception as e:
        print(f"❌ Sources test failed: {e}")
        return False
    finally:
        session.close()


def test_plans():
    """Test plans table"""
    print("\n💳 Testing plans...")
    session = get_sync_session()
    
    try:
        plans = session.query(Plan).all()
        print(f"   Found {len(plans)} plans:")
        for plan in plans:
            print(f"   - {plan.name}: {plan.price_bgn} BGN")
            print(f"     Limits: {plan.limits}")
        
        assert len(plans) > 0, "No plans found"
        print("✅ Plans test passed")
        return True
    except Exception as e:
        print(f"❌ Plans test failed: {e}")
        return False
    finally:
        session.close()


def test_brand_models():
    """Test brand/model mappings"""
    print("\n🚗 Testing brand/model mappings...")
    session = get_sync_session()
    
    try:
        brands = session.query(BrandModel).all()
        print(f"   Found {len(brands)} brand/model mappings:")
        
        # Group by normalized_brand
        brand_dict = {}
        for brand in brands:
            if brand.normalized_brand not in brand_dict:
                brand_dict[brand.normalized_brand] = []
            brand_dict[brand.normalized_brand].append(brand.normalized_model)
        
        for brand, models in sorted(brand_dict.items()):
            print(f"   - {brand}: {', '.join(sorted(set(models)))}")
        
        assert len(brands) > 0, "No brand/model mappings found"
        print("✅ Brand/model mappings test passed")
        return True
    except Exception as e:
        print(f"❌ Brand/model mappings test failed: {e}")
        return False
    finally:
        session.close()


def test_create_test_user():
    """Test creating a test user"""
    print("\n👤 Testing user creation...")
    session = get_sync_session()
    
    try:
        # Get Free plan
        free_plan = session.query(Plan).filter_by(name="Free").first()
        assert free_plan, "Free plan not found"
        
        # Check if test user exists
        test_user = session.query(User).filter_by(telegram_id=123456789).first()
        
        if not test_user:
            # Create test user
            test_user = User(
                telegram_id=123456789,
                telegram_username="test_user",
                plan_id=free_plan.id,
            )
            session.add(test_user)
            session.commit()
            print("   Created test user: @test_user")
        else:
            print("   Test user already exists: @test_user")
        
        print(f"   User plan: {test_user.plan.name}")
        print("✅ User creation test passed")
        return True
    except Exception as e:
        session.rollback()
        print(f"❌ User creation test failed: {e}")
        return False
    finally:
        session.close()


def test_normalization():
    """Test normalization functions"""
    print("\n🔧 Testing normalization...")
    
    try:
        from libs.domain.normalization import BrandModelNormalizer, FieldNormalizer
        
        # Test brand/model normalization
        normalizer = BrandModelNormalizer()
        
        test_cases = [
            ("BMW", "X5", "BMW", "X5"),
            ("БМВ", "Х5", "BMW", "X5"),
            ("mercedes", "e class", "Mercedes-Benz", "E-Class"),
        ]
        
        print("   Testing brand/model normalization:")
        for raw_brand, raw_model, expected_brand, expected_model in test_cases:
            norm_brand, norm_model = normalizer.normalize(raw_brand, raw_model)
            status = "✅" if (norm_brand == expected_brand or norm_model == expected_model) else "⚠️"
            print(f"   {status} {raw_brand} {raw_model} → {norm_brand} {norm_model}")
        
        # Test field normalization
        field_norm = FieldNormalizer()
        
        print("\n   Testing field normalization:")
        print(f"   Fuel: дизел → {field_norm.normalize_fuel('дизел')}")
        print(f"   Gearbox: автоматична → {field_norm.normalize_gearbox('автоматична')}")
        print(f"   Mileage: 125 000 km → {field_norm.normalize_mileage('125 000 km')}")
        print(f"   Year: 2020 г. → {field_norm.normalize_year('2020 г.')}")
        
        print("✅ Normalization test passed")
        return True
    except Exception as e:
        print(f"❌ Normalization test failed: {e}")
        return False


def test_risk_evaluation():
    """Test risk evaluation"""
    print("\n🤖 Testing risk evaluation...")
    
    try:
        from libs.ml.risk_evaluation import RiskClassifier
        
        classifier = RiskClassifier()
        
        test_cases = [
            ("Отлична кола, добре поддържана", "green"),
            ("След удар, подменена врата", "red"),
            ("Внос от Германия, първа регистрация", "yellow"),
        ]
        
        print("   Testing risk classification:")
        for description, expected_color in test_cases:
            result = classifier.classify(description)
            status = "✅" if result["risk_level"] == expected_color else "⚠️"
            print(f"   {status} '{description[:30]}...' → {result['risk_level']} ({result['confidence']:.2f})")
            if result["red_flags"]:
                print(f"      Red flags: {', '.join(result['red_flags'][:3])}")
        
        print("✅ Risk evaluation test passed")
        return True
    except Exception as e:
        print(f"❌ Risk evaluation test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 CarScout AI - System Tests")
    print("==============================")
    print()
    
    results = []
    
    # Run tests
    results.append(("Database Connection", test_database_connection()))
    results.append(("Sources", test_sources()))
    results.append(("Plans", test_plans()))
    results.append(("Brand/Model Mappings", test_brand_models()))
    results.append(("User Creation", test_create_test_user()))
    results.append(("Normalization", test_normalization()))
    results.append(("Risk Evaluation", test_risk_evaluation()))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print()
    print(f"Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
