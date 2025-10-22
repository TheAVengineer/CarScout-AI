"""Debug year and price extraction"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from libs.domain.database import sync_engine
from libs.domain.models import ListingRaw
from bs4 import BeautifulSoup
import re

with Session(sync_engine) as session:
    listing = session.query(ListingRaw).filter(
        ListingRaw.raw_html.isnot(None),
        ListingRaw.url.like('%honda%')
    ).first()
    print(f'\nURL: {listing.url}\n')
    
    # Check title extraction
    soup = BeautifulSoup(listing.raw_html, 'html.parser')
    title_elem = soup.select_one('title')
    title = title_elem.text.strip() if title_elem else 'NO TITLE'
    print(f'Title: {title[:150]}...\n')
    
    # Check year regex
    year_match = re.search(r'(\d{4})\s*г', title)
    print(f'Year regex pattern: r"(\\d{{4}})\\s*г"')
    print(f'Year match: {year_match.group(1) if year_match else "NO MATCH"}\n')
    
    # Check price regex - show all matches
    price_matches = re.findall(r'(\d[\d\s]{2,8})\s*(лв|€|EUR)', listing.raw_html)
    print(f'Price regex pattern: r"(\\d[\\d\\s]{{2,8}})\\s*(лв|€|EUR)"')
    print(f'Total price matches: {len(price_matches)}')
    print(f'First 10 matches: {price_matches[:10]}')
    
    # Look for the actual price in title
    print(f'\n--- Searching for price near "Цена" ---')
    price_section = re.search(r'Цена.{0,100}', listing.raw_html, re.IGNORECASE)
    if price_section:
        print(f'Found: {price_section.group(0)[:100]}')
    
    # Try to find large numbers (likely prices)
    large_numbers = re.findall(r'(\d{4,6})\s*(лв|EUR)', listing.raw_html)
    print(f'\nLarge numbers (4-6 digits): {large_numbers[:10]}')
