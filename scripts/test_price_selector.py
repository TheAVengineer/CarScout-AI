"""Test what .Price::text actually extracts from saved HTML."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from configs.settings import BaseSettings
from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw
from scrapy.selector import Selector

settings = BaseSettings()

# Get database session
db = get_sync_session()

# Get a recent listing with price
listing = db.query(ListingRaw).filter(
    ListingRaw.raw_html.isnot(None)
).order_by(ListingRaw.created_at.desc()).first()

if not listing:
    print("❌ No listings with HTML found")
    sys.exit(1)

print(f"Testing listing: {listing.url}\n")

# Create Scrapy selector
selector = Selector(text=listing.raw_html)

# Test different extraction methods
print("1. Using ::text (what spider uses):")
price_text = selector.css('.Price::text').get() or ''
print(f"   Result: {repr(price_text)}")

print("\n2. Using .get() (all text content):")
price_all = selector.css('.Price').get() or ''
print(f"   Result: {repr(price_all)}")

print("\n3. Using getall() (all text nodes):")
price_texts = selector.css('.Price::text').getall()
print(f"   Result: {price_texts}")

print("\n4. Full element extraction:")
price_elem = selector.css('.Price')
if price_elem:
    all_text = price_elem.xpath('.//text()').getall()
    print(f"   All text nodes: {all_text}")
    joined = ' '.join(all_text)
    print(f"   Joined: {repr(joined)}")

# Test the regex on different versions
import re

print("\n5. Regex tests:")
for text in [price_text, ' '.join(price_texts) if price_texts else '', ' '.join(price_elem.xpath('.//text()').getall()) if price_elem else '']:
    if text:
        bgn_match = re.search(r'(\d+(?:\s+\d+)*)\s*лв', text)
        print(f"   Text: {repr(text[:50])}")
        print(f"   BGN match: {bgn_match.group(1) if bgn_match else 'None'}")
