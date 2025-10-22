"""
Test the updated Mobile.bg parser with real data from database.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from libs.domain.database import sync_engine
from libs.domain.models import ListingRaw
from workers.pipeline.tasks.parse import MobileBgParser


def test_parser():
    """Test parser with real Mobile.bg listings."""
    print("\n=== Testing Mobile.bg Parser ===\n")
    
    with Session(sync_engine) as session:
        # Get first 3 listings with raw HTML
        listings = session.query(ListingRaw).filter(
            ListingRaw.raw_html.isnot(None)
        ).limit(3).all()
        
        if not listings:
            print("❌ No listings with raw_html found!")
            return
        
        print(f"Found {len(listings)} listings to test\n")
        
        for i, listing_raw in enumerate(listings, 1):
            print(f"{'='*60}")
            print(f"Listing {i}: {listing_raw.url}")
            print(f"{'='*60}")
            
            # Parse the HTML
            try:
                parsed = MobileBgParser.parse(
                    html=listing_raw.raw_html,
                    url=listing_raw.url
                )
                
                # DEBUG: Check year extraction
                from bs4 import BeautifulSoup
                import re
                soup = BeautifulSoup(listing_raw.raw_html, 'html.parser')
                title_elem = soup.select_one('title')
                title_full = title_elem.text.strip() if title_elem else None
                year_match = re.search(r'(\d{4})\s*г', title_full) if title_full else None
                print(f"  DEBUG - Title: {title_full[:80] if title_full else 'None'}...")
                print(f"  DEBUG - Year match: {year_match.group(1) if year_match else 'No match'}")
                
                # Display extracted data
                print(f"\n✅ EXTRACTED DATA:")
                print(f"  Title:      {parsed.get('title', 'N/A')[:60]}...")
                print(f"  Brand:      {parsed.get('brand', 'N/A')}")
                print(f"  Model:      {parsed.get('model', 'N/A')}")
                print(f"  Year:       {parsed.get('year', 'N/A')}")
                print(f"  Price:      {parsed.get('price', 'N/A')} {parsed.get('currency', 'N/A')}")
                print(f"  Mileage:    {parsed.get('mileage_km', 'N/A')} km")
                print(f"  Fuel:       {parsed.get('fuel_type', 'N/A')}")
                print(f"  Gearbox:    {parsed.get('gearbox', 'N/A')}")
                print(f"  Body Type:  {parsed.get('body_type', 'N/A')}")
                print(f"  Images:     {len(parsed.get('images', []))} images")
                
                # Check if key fields are extracted
                missing = []
                if not parsed.get('brand'):
                    missing.append('brand')
                if not parsed.get('model'):
                    missing.append('model')
                if not parsed.get('price'):
                    missing.append('price')
                
                if missing:
                    print(f"\n⚠️  Missing fields: {', '.join(missing)}")
                else:
                    print(f"\n✅ All key fields extracted successfully!")
                
            except Exception as e:
                print(f"\n❌ PARSER ERROR: {e}")
                import traceback
                traceback.print_exc()
            
            print()


if __name__ == "__main__":
    test_parser()
