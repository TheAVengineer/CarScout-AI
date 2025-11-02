"""Inspect HTML to find correct price selector"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw
import re
from bs4 import BeautifulSoup

session = get_sync_session()

# Get one of the successfully scraped listings
listing = session.query(ListingRaw).filter(
    ListingRaw.site_ad_id == '11758305565394920'
).first()

if listing and listing.raw_html:
    soup = BeautifulSoup(listing.raw_html, 'html.parser')
    
    print("=" * 70)
    print("SEARCHING FOR PRICE IN HTML")
    print("=" * 70)
    
    # Method 1: Find all elements with "price" in class
    print("\n1. Elements with 'price' in class:")
    price_elements = soup.find_all(class_=re.compile('price', re.I))
    for elem in price_elements[:10]:
        text = elem.get_text(strip=True)
        if text:
            print(f"  Class: {elem.get('class')} -> Text: {text[:100]}")
    
    # Method 2: Search for BGN/EUR/лв pattern
    print("\n2. Text containing 'лв' (BGN currency):")
    lev_pattern = re.compile(r'(\d[\d\s]+)\s*лв')
    matches = lev_pattern.findall(listing.raw_html)
    for match in matches[:10]:
        clean = match.replace(' ', '').replace('\xa0', '')
        if clean.isdigit():
            print(f"  Found: {match} -> Clean: {clean}")
    
    # Method 3: Look for specific price div/span
    print("\n3. Looking for common price containers:")
    for selector in ['.price', '#price', '.adPrice', '.advPrice', '[itemprop="price"]', '.priceField']:
        elem = soup.select_one(selector)
        if elem:
            print(f"  {selector}: {elem.get_text(strip=True)[:100]}")
    
    # Method 4: Search raw HTML
    print("\n4. Raw HTML search for price patterns:")
    price_html = re.findall(r'<[^>]*price[^>]*>([^<]+)', listing.raw_html[:50000], re.I)
    for match in price_html[:10]:
        text = match.strip()
        if text and ('лв' in text or 'EUR' in text or text.isdigit()):
            print(f"  {text}")
    
    print("\n" + "=" * 70)
else:
    print("Listing not found or has no HTML")

session.close()
