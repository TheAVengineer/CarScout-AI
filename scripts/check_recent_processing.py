"""Check if Celery worker is processing listings with the new parser."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from libs.domain.database import sync_engine
from libs.domain.models import ListingRaw, ListingNormalized, Score
from datetime import datetime, timedelta

with Session(sync_engine) as session:
    # Check recently processed listings (last 5 minutes)
    recent_time = datetime.utcnow() - timedelta(minutes=5)
    
    recent_normalized = session.query(ListingNormalized).filter(
        ListingNormalized.created_at >= recent_time
    ).order_by(ListingNormalized.created_at.desc()).limit(5).all()
    
    print(f'\n{"="*70}')
    print(f'CELERY WORKER PROCESSING STATUS')
    print(f'{"="*70}\n')
    
    print(f'Recently normalized listings (last 5 min): {len(recent_normalized)}\n')
    
    if recent_normalized:
        for listing in recent_normalized:
            brand_name = listing.brand_id or "Unknown"
            model_name = listing.model_id or "Unknown"
            
            print(f'✅ {brand_name} {model_name} ({listing.year})')
            print(f'  Price: {listing.price_bgn} BGN')
            print(f'  Created: {listing.created_at}')
            
            # Check if it has a score
            score = session.query(Score).filter(Score.listing_id == listing.id).first()
            if score:
                print(f'  Score: {score.score}/10 ({score.final_state})')
                if score.reasons:
                    print(f'  Reasons: {", ".join(score.reasons[:2])}...')
            print()
    else:
        print('⏳ No new listings processed yet. This is normal if worker just started.\n')
        
        total = session.query(ListingNormalized).count()
        print(f'Total normalized listings in database: {total}')
        
        # Show the most recent ones
        recent = session.query(ListingNormalized).order_by(
            ListingNormalized.created_at.desc()
        ).limit(3).all()
        
        print(f'\nMost recent normalized listings (may be from old parser):')
        for listing in recent:
            brand_name = listing.brand_id or "Unknown"
            model_name = listing.model_id or "Unknown"
            print(f'  • {brand_name} {model_name} ({listing.year}) - {listing.price_bgn} BGN')
            print(f'    Created: {listing.created_at}')
        
        print(f'\n💡 TIP: Celery worker processes listings when they are scraped.')
        print(f'   The scraper runs every 2 minutes (Mobile.bg) and 3 minutes (Cars.bg).')
        print(f'   Or manually trigger processing by running a test.\n')
    
    # Check queue length
    import redis
    r = redis.Redis(host='localhost', port=6379, db=1, decode_responses=False)
    queue_len = r.llen('celery')
    print(f'Current Celery queue length: {queue_len} pending tasks\n')
