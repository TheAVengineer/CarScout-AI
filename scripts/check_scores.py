"""Check recent scores"""
from libs.domain.database import get_sync_session
from libs.domain.models import Score
from sqlalchemy import desc

with get_sync_session() as session:
    scores = session.query(Score).order_by(desc(Score.scored_at)).limit(5).all()
    
    if scores:
        print(f"✅ Found {len(scores)} recent scores:")
        for s in scores:
            print(f"   Listing: {str(s.listing_id)[:8]}... → Score: {s.score:.1f}/10, State: {s.final_state}, Time: {s.scored_at}")
    else:
        print("❌ No scores found in database")
