"""Check how many Audi listings exist for comparables."""
from libs.domain.database import get_sync_session
from libs.domain.models import ListingNormalized

with get_sync_session() as session:
    # Count non-duplicate Audi listings
    audis = session.query(ListingNormalized).filter_by(
        brand_id='audi',
        is_duplicate=False
    ).all()
    
    print(f"\n📊 Non-duplicate Audi listings: {len(audis)}")
    
    for car in audis[:10]:
        print(f"  {car.brand_id} {car.model_id} {car.year} - {car.price_bgn} BGN ({car.fuel}, {car.gearbox})")
    
    # Count Audi A4 specifically
    a4s = session.query(ListingNormalized).filter_by(
        brand_id='audi',
        model_id='a4',
        is_duplicate=False
    ).all()
    
    print(f"\n📊 Non-duplicate Audi A4 listings: {len(a4s)}")
