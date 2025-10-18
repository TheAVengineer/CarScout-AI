"""
Pytest configuration
"""
import pytest
import os

# Set test environment
os.environ["ENV"] = "test"


@pytest.fixture
def sample_listing():
    """Sample listing data for testing"""
    return {
        "listing_id": "123e4567-e89b-12d3-a456-426614174000",
        "brand": "BMW",
        "model": "X5",
        "year": 2018,
        "mileage_km": 120000,
        "fuel": "diesel",
        "gearbox": "automatic",
        "body": "suv",
        "price_bgn": 32000,
        "region": "Sofia",
    }


@pytest.fixture
def sample_event():
    """Sample event payload for testing"""
    from datetime import datetime
    from uuid import UUID
    
    return {
        "listing_id": UUID("123e4567-e89b-12d3-a456-426614174000"),
        "source_id": "mobile_bg",
        "site_ad_id": "12345",
        "url": "https://mobile.bg/ad12345",
        "listing_version": 1,
        "first_seen_at": datetime.now(),
        "last_seen_at": datetime.now(),
        "is_active": True,
        "is_duplicate": False,
    }
