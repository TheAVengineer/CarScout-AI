"""Check why Audi A4 is marked as duplicate."""
from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw, ListingNormalized, DuplicateLog

with get_sync_session() as session:
    # Find the Audi A4 listing
    raw = session.query(ListingRaw).filter(
        ListingRaw.url.like('%audi-a4-s-line-kozha%')
    ).first()
    
    normalized = session.query(ListingNormalized).filter_by(
        raw_id=raw.id
    ).first()
    
    print(f"\n🔍 Audi A4 Listing: {normalized.id}")
    print(f"  Brand: {normalized.brand_id}, Model: {normalized.model_id}")
    print(f"  Year: {normalized.year}, Price: {normalized.price_bgn} BGN")
    print(f"  Is Duplicate: {normalized.is_duplicate}")
    print(f"  Duplicate Of: {normalized.duplicate_of}")
    
    if normalized.duplicate_of:
        dup = session.query(ListingNormalized).filter_by(
            id=normalized.duplicate_of
        ).first()
        print(f"\n📋 Duplicate Master Listing:")
        print(f"  ID: {dup.id}")
        print(f"  Brand: {dup.brand_id}, Model: {dup.model_id}")
        print(f"  Year: {dup.year}, Price: {dup.price_bgn} BGN")
    
    # Check duplicate logs
    logs = session.query(DuplicateLog).filter_by(
        listing_id=normalized.id
    ).all()
    
    print(f"\n📊 Duplicate Detection Logs ({len(logs)} entries):")
    for log in logs[:5]:
        print(f"  Method: {log.method}, Score: {log.score:.2f}")
        print(f"    Duplicate of: {log.duplicate_of}")
        
        if log.duplicate_of:
            dup_listing = session.query(ListingNormalized).filter_by(
                id=log.duplicate_of
            ).first()
            if dup_listing:
                print(f"    → {dup_listing.brand_id} {dup_listing.model_id} {dup_listing.year} - {dup_listing.price_bgn} BGN")
