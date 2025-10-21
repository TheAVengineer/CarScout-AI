"""Check recent pipeline activity"""
from libs.domain.database import get_sync_session
from libs.domain.models import ListingNormalized, Score, CompCache
from sqlalchemy import desc
from datetime import datetime, timedelta

with get_sync_session() as session:
    # Check recent normalized listings
    recent_time = datetime.now() - timedelta(minutes=10)
    
    print("=" * 60)
    print("📊 Recent Pipeline Activity (last 10 minutes)")
    print("=" * 60)
    
    normalized = session.query(ListingNormalized).filter(
        ListingNormalized.created_at >= recent_time
    ).order_by(desc(ListingNormalized.created_at)).all()
    
    if normalized:
        print(f"\n✅ Normalized Listings: {len(normalized)}")
        for n in normalized:
            print(f"   {str(n.id)[:8]}... → {n.brand_id} {n.model_id}, created: {n.created_at}")
    else:
        print("\n❌ No normalized listings in last 10 minutes")
    
    # Check recent comp caches
    comp_caches = session.query(CompCache).filter(
        CompCache.computed_at >= recent_time
    ).order_by(desc(CompCache.computed_at)).all()
    
    if comp_caches:
        print(f"\n✅ Comparable Caches: {len(comp_caches)}")
        for c in comp_caches:
            print(f"   {str(c.listing_id)[:8]}... → {c.comp_count} comps, discount: {c.discount_pct:.1f}%")
    else:
        print("\n❌ No comp caches in last 10 minutes")
    
    # Check recent scores
    scores = session.query(Score).filter(
        Score.scored_at >= recent_time
    ).order_by(desc(Score.scored_at)).all()
    
    if scores:
        print(f"\n✅ Scores: {len(scores)}")
        for s in scores:
            print(f"   {str(s.listing_id)[:8]}... → {s.score:.1f}/10, state: {s.final_state}")
    else:
        print("\n❌ No scores in last 10 minutes")
    
    print("\n" + "=" * 60)
