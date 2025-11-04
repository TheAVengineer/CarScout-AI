#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw
from sqlalchemy import func

# Get database stats
session = get_sync_session()

total = session.query(func.count(ListingRaw.id)).scalar()
active = session.query(func.count(ListingRaw.id)).filter(ListingRaw.is_active == True).scalar()
inactive = total - active

session.close()

# Display results
print(f"📊 Total Listings:  {total:,}")
print(f"✅ Active:          {active:,} ({(active/total)*100:.1f}%)")
print(f"❌ Inactive:        {inactive:,} ({(inactive/total)*100:.1f}%)")
print(f"\n🎯 Target: 100,000 listings")
print(f"Progress: {total:,} / 100,000 ({(total/100000)*100:.1f}%)")
