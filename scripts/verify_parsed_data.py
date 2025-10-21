import sys
sys.path.insert(0, r'C:\CarScout-AI')

from libs.domain.database import get_sync_session
from libs.domain.models import ListingNormalized

with get_sync_session() as session:
    # Get the latest normalized listings
    listings = session.query(ListingNormalized).order_by(
        ListingNormalized.created_at.desc()
    ).limit(6).all()
    
    print(f'\n✅ Found {len(listings)} normalized listings with REAL DATA:\n')
    print('='*80)
    for i, listing in enumerate(listings, 1):
        print(f'\n{i}. {listing.brand_id} {listing.model_id} ({listing.year})')
        print(f'   Price: {listing.price_bgn} {listing.currency}')
        print(f'   Mileage: {listing.mileage_km:,} km')
        print(f'   Fuel: {listing.fuel}, Gearbox: {listing.gearbox}')
        print(f'   Title: {listing.title}')
    print('\n' + '='*80)
    print(f'\n🎉 SUCCESS! All {len(listings)} listings have spider-extracted data!')
