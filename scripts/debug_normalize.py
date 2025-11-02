"""
Debug what data the normalize task receives
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from libs.domain.database import sync_engine
from libs.domain.models import ListingRaw, ListingNormalized

# Check what data is in the Audi listing after parse
with Session(sync_engine) as session:
    raw = session.query(ListingRaw).filter(
        ListingRaw.url.like('%audi-a4-s-line-kozha%')
    ).first()
    
    if raw:
        print(f"Raw listing: {raw.url}\n")
        
        # Check if normalized exists
        normalized = session.query(ListingNormalized).filter(
            ListingNormalized.raw_id == raw.id
        ).first()
        
        if normalized:
            print(f"Normalized listing found:")
            print(f"  Brand ID: {normalized.brand_id}")
            print(f"  Model ID: {normalized.model_id}")
            print(f"  Year: {normalized.year}")
            print(f"  Price: {normalized.price_bgn} BGN")
            print(f"  Mileage: {normalized.mileage_km}")
            print(f"  Version: {normalized.listing_version}")
        else:
            print("No normalized listing found yet")
