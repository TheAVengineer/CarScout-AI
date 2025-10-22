#!/usr/bin/env python
"""Analyze Mobile.bg HTML to extract proper selectors"""
import sys
import os
import re
import json
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw

def analyze_listing(listing):
    """Analyze a single listing HTML"""
    print(f"\n{'='*80}")
    print(f"URL: {listing.url}")
    print(f"Site ID: {listing.site_ad_id}")
    
    if not listing.raw_html:
        print("No HTML available")
        return
    
    html = listing.raw_html
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract title
    title = soup.find('title')
    print(f"\nTitle: {title.get_text() if title else 'NOT FOUND'}")
    
    # Try to find price
    price_patterns = [
        r'(\d[\d\s]{2,8})\s*лв',
        r'(\d[\d\s]{2,8})\s*€',
        r'"price"[:\s]*(\d+)',
    ]
    
    for pattern in price_patterns:
        matches = re.findall(pattern, html)
        if matches:
            print(f"Price matches ({pattern}): {matches[:3]}")
            break
    
    # Find brand/model in URL
    url_match = re.search(r'obiava-\d+-([^-]+)-([^-/]+)', listing.url)
    if url_match:
        print(f"URL brand: {url_match.group(1)}")
        print(f"URL model: {url_match.group(2)}")
    
    # Look for structured data (JSON-LD)
    json_ld = soup.find('script', type='application/ld+json')
    if json_ld:
        try:
            data = json.loads(json_ld.string)
            print(f"\nJSON-LD data found:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
        except:
            pass
    
    # Look for specific table rows (Mobile.bg uses tables)
    tables = soup.find_all('table')
    print(f"\nTables found: {len(tables)}")
    
    if listing.parsed_data:
        print(f"\nParsed Data:")
        print(json.dumps(listing.parsed_data, indent=2, ensure_ascii=False))

def main():
    session = get_sync_session()
    
    # Get listings with HTML
    listings = session.query(ListingRaw).filter(
        ListingRaw.raw_html.isnot(None)
    ).limit(3).all()
    
    print(f"Found {len(listings)} listings with HTML")
    
    for listing in listings:
        analyze_listing(listing)
    
    session.close()

if __name__ == "__main__":
    main()
