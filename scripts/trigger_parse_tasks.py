import sys
sys.path.insert(0, r'C:\CarScout-AI')

from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw
from workers.pipeline.tasks.parse import parse_listing

with get_sync_session() as session:
    listings = session.query(ListingRaw).filter(
        ListingRaw.site_ad_id.in_(['91759926375488155', '11758654789789494', '11759240042296408'])
    ).all()
    
    print(f'Triggering parse for {len(listings)} listings...')
    results = [parse_listing.delay(str(l.id)) for l in listings]
    print(f'Triggered {len(results)} tasks')
    for i, r in enumerate(results):
        print(f'  Task {i+1}: {r.id}')
