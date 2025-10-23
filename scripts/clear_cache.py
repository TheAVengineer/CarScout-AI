"""Clear comparables cache for Audi A4 listing."""
from libs.domain.database import get_sync_session
from libs.domain.models import CompCache
from uuid import UUID

listing_id = UUID('61561569-b003-47b3-ac27-538b6ba16c34')

with get_sync_session() as session:
    cache = session.query(CompCache).filter_by(listing_id=listing_id).first()
    
    if cache:
        print(f"🗑️  Found cached price data:")
        print(f"   Predicted: {cache.predicted_price_bgn} BGN")
        print(f"   Sample size: {cache.sample_size}")
        print(f"   Computed at: {cache.computed_at}")
        print(f"\n   Deleting...")
        
        session.delete(cache)
        session.commit()
        
        print("✅ Cache cleared!")
    else:
        print("ℹ️  No cache found")
