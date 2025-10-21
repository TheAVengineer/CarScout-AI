import sys
sys.path.insert(0, r'C:\CarScout-AI')

from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw
from bs4 import BeautifulSoup

with get_sync_session() as session:
    # Get one of the scraped listings
    listing = session.query(ListingRaw).filter(
        ListingRaw.site_ad_id == '11758654789789494'
    ).first()
    
    if listing:
        print(f"Listing URL: {listing.url}")
        print(f"HTML length: {len(listing.raw_html) if listing.raw_html else 0} chars")
        print(f"\nFirst 500 chars of HTML:")
        if listing.raw_html:
            print(listing.raw_html[:500])
            
            # Try to find the title
            soup = BeautifulSoup(listing.raw_html, 'html.parser')
            title = soup.find('h1')
            print(f"\nFound title tag: {title.text if title else 'None'}")
            
            # Check for price
            price_elem = soup.select_one('.price, .adPage__price, [class*="price"]')
            print(f"Found price element: {price_elem.text if price_elem else 'None'}")
        else:
            print("No HTML content!")
    else:
        print("Listing not found!")
