#!/usr/bin/env python
"""
Seed database with initial data
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.domain.database import get_sync_session
from libs.domain.models import Source, Plan, BrandModel
from libs.domain.normalization import seed_brand_models


def seed_sources():
    """Seed marketplace sources"""
    session = get_sync_session()
    
    sources_data = [
        {
            "name": "mobile_bg",
            "base_url": "https://www.mobile.bg",
            "enabled": True,
            "crawl_interval_s": 120,
        },
        {
            "name": "cars_bg",
            "base_url": "https://www.cars.bg",
            "enabled": True,
            "crawl_interval_s": 180,
        },
        {
            "name": "olx_bg",
            "base_url": "https://www.olx.bg",
            "enabled": False,  # Not implemented yet
            "crawl_interval_s": 300,
        },
    ]
    
    for source_data in sources_data:
        existing = session.query(Source).filter_by(name=source_data["name"]).first()
        if not existing:
            source = Source(**source_data)
            session.add(source)
            print(f"✅ Added source: {source_data['name']}")
        else:
            print(f"⏭️  Source already exists: {source_data['name']}")
    
    session.commit()
    session.close()


def seed_plans_data():
    """Seed subscription plans"""
    session = get_sync_session()
    
    plans_data = [
        {
            "name": "Free",
            "limits": {"max_alerts": 3, "delay_minutes": 30, "daily_alert_cap": 10},
            "price_bgn": 0,
        },
        {
            "name": "Premium",
            "limits": {"max_alerts": 10, "delay_minutes": 0, "daily_alert_cap": 50},
            "price_bgn": 19.99,
        },
        {
            "name": "Pro",
            "limits": {"max_alerts": 999, "delay_minutes": 0, "daily_alert_cap": 999},
            "price_bgn": 39.99,
        },
    ]
    
    for plan_data in plans_data:
        existing = session.query(Plan).filter_by(name=plan_data["name"]).first()
        if not existing:
            plan = Plan(**plan_data)
            session.add(plan)
            print(f"✅ Added plan: {plan_data['name']}")
        else:
            print(f"⏭️  Plan already exists: {plan_data['name']}")
    
    session.commit()
    session.close()


def main():
    """Run all seed functions"""
    print("🌱 Seeding database...")
    print()
    
    print("📦 Seeding sources...")
    seed_sources()
    print()
    
    print("💳 Seeding plans...")
    seed_plans_data()
    print()
    
    print("🚗 Seeding brand/model mappings...")
    seed_brand_models()
    print()
    
    print("✅ Database seeding complete!")


if __name__ == "__main__":
    main()
