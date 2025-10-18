#!/usr/bin/env python
"""
Test the Alert Matcher DSL and matching logic
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.domain.alert_matcher import AlertQueryParser, AlertMatcher
from libs.domain.database import get_sync_session
from libs.domain.models import User, Alert, ListingNormalized, UserPlan


def test_dsl_parser():
    """Test the DSL parser with various queries"""
    print("🧪 Testing Alert DSL Parser")
    print("=" * 60)
    
    test_queries = [
        "BMW X5 diesel <25000 2016+ <180000km automatic Sofia",
        "Audi A4 petrol 2018+ <15000",
        "Mercedes C-Class >200hp 2015-2020 automatic",
        "VW Golf <10000 2010+ manual Plovdiv",
        "Toyota RAV4 hybrid 2019+ Varna",
        "БМВ X3 дизел <30000 2017+ автоматична",
        "Мерцедес Е-Класа >250кс 2016-2022 София",
        "джип 2018+ <25000 автоматична дизел",
    ]
    
    parser = AlertQueryParser()
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        result = parser.parse(query)
        
        print("   Parsed:")
        for key, value in result.items():
            if value is not None:
                print(f"     {key}: {value}")
    
    print("\n✅ DSL Parser test complete!")


def test_alert_matching():
    """Test alert matching with sample data"""
    print("\n\n🧪 Testing Alert Matching")
    print("=" * 60)
    
    session = get_sync_session()
    
    # Create test user with plan
    print("\n📝 Creating test user...")
    user = User(
        telegram_id=12345678,
        telegram_username="test_user",
        plan=UserPlan.FREE,
        alerts_quota_daily=10,
    )
    session.add(user)
    session.commit()
    print(f"   ✅ User created: {user.telegram_id}")
    
    # Create test alerts
    print("\n📝 Creating test alerts...")
    alerts_data = [
        {
            "query": "BMW X5 diesel <35000 2015+ automatic",
            "is_active": True,
        },
        {
            "query": "Audi Q7 2018+ <40000",
            "is_active": True,
        },
        {
            "query": "Mercedes GLE diesel 2016+ Sofia",
            "is_active": False,  # Inactive
        },
    ]
    
    for alert_data in alerts_data:
        alert = Alert(
            user_id=user.id,
            **alert_data
        )
        session.add(alert)
    
    session.commit()
    print(f"   ✅ Created {len(alerts_data)} alerts")
    
    # Create test listing that matches first alert
    print("\n📝 Creating test listing...")
    listing = ListingNormalized(
        site_ad_id="test_match_123",
        url="https://www.mobile.bg/test/123",
        normalized_brand="BMW",
        normalized_model="X5",
        price_bgn=32000,
        year=2017,
        mileage_km=145000,
        normalized_fuel="diesel",
        normalized_gearbox="automatic",
        normalized_region="София-град",
        state="approved",
    )
    session.add(listing)
    session.commit()
    print(f"   ✅ Listing created: {listing.normalized_brand} {listing.normalized_model}")
    
    # Test matching
    print("\n🔍 Testing alert matching...")
    matcher = AlertMatcher(session)
    
    matches = matcher.find_matching_alerts(listing)
    
    print(f"\n📊 Found {len(matches)} matching alerts:")
    for alert in matches:
        print(f"   ✅ Alert: '{alert.query}'")
        print(f"      User: {alert.user.telegram_username}")
        print(f"      Active: {alert.is_active}")
    
    # Clean up
    print("\n🧹 Cleaning up test data...")
    session.delete(listing)
    for alert in session.query(Alert).filter_by(user_id=user.id).all():
        session.delete(alert)
    session.delete(user)
    session.commit()
    session.close()
    
    print("✅ Alert matching test complete!")
    
    return len(matches) == 1  # Should match first alert only


def main():
    """Run all alert matcher tests"""
    print("🧪 CarScout AI - Alert Matcher Tests\n")
    
    # Test DSL parser
    test_dsl_parser()
    
    # Test alert matching
    try:
        success = test_alert_matching()
        
        print("\n" + "=" * 60)
        if success:
            print("✅ All alert matcher tests PASSED!")
        else:
            print("❌ Alert matcher tests FAILED")
            return 1
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
