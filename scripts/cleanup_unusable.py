"""
Cleanup script - Delete unusable listings from database

Removes listings that have:
- raw_html_path set (indicates file was supposed to be saved)
- raw_html is NULL (no HTML in database)  
- parsed_data is NULL (no spider-extracted data)

These listings cannot be processed because HTML files don't exist on disk.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw


def cleanup_unusable_listings():
    """Delete listings that cannot be processed"""
    print("=" * 70)
    print("🧹 CARSCOUT AI - DATABASE CLEANUP")
    print("=" * 70)
    print()
    
    session = get_sync_session()
    
    try:
        # Find unusable listings
        print("🔍 Finding unusable listings...")
        unusable = session.query(ListingRaw).filter(
            ListingRaw.raw_html == None,
            ListingRaw.raw_html_path != None,
            ListingRaw.parsed_data == None
        ).all()
        
        print(f"   Found {len(unusable)} unusable listings")
        print()
        
        if len(unusable) == 0:
            print("✅ No unusable listings found!")
            return
        
        # Show sample
        print("📋 Sample of listings to delete:")
        for listing in unusable[:5]:
            print(f"   - {listing.site_ad_id}: {listing.raw_html_path}")
        if len(unusable) > 5:
            print(f"   ... and {len(unusable) - 5} more")
        print()
        
        # Confirm deletion
        response = input(f"⚠️  Delete {len(unusable)} listings? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Cleanup cancelled")
            return
        
        print()
        print("🗑️  Deleting listings...")
        
        deleted_count = 0
        for i, listing in enumerate(unusable, 1):
            session.delete(listing)
            deleted_count += 1
            
            if i % 100 == 0:
                print(f"   [{i}/{len(unusable)}] Deleted...")
                session.commit()  # Commit in batches
        
        session.commit()
        
        print()
        print(f"✅ Successfully deleted {deleted_count} unusable listings!")
        print()
        
        # Show remaining listings
        remaining = session.query(ListingRaw).count()
        print(f"📊 Remaining raw listings: {remaining}")
        
        # Show breakdown
        with_html = session.query(ListingRaw).filter(
            ListingRaw.raw_html != None
        ).count()
        
        with_parsed_data = session.query(ListingRaw).filter(
            ListingRaw.parsed_data != None
        ).count()
        
        print(f"   - With raw_html: {with_html}")
        print(f"   - With parsed_data: {with_parsed_data}")
        print()
        print("💡 Database is now clean and ready for fresh scraping!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    cleanup_unusable_listings()
