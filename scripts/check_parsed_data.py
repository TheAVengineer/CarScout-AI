"""Check what the parse task actually stored."""
from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw
import json

with get_sync_session() as session:
    # Find the Audi A4 listing
    raw = session.query(ListingRaw).filter(
        ListingRaw.url.like('%audi-a4-s-line-kozha%')
    ).first()
    
    if raw:
        print(f"\n📄 Raw listing: {raw.url}")
        print(f"\n🔍 Parsed Data:")
        if raw.parsed_data:
            print(json.dumps(raw.parsed_data, indent=2, ensure_ascii=False))
        else:
            print("  None - parse task hasn't stored anything!")
    else:
        print("Listing not found!")
