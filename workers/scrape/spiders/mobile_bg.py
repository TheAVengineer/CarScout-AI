"""
Mobile.bg spider
"""
import re
import hashlib
from datetime import datetime
from uuid import uuid4

import scrapy
from scrapy_playwright.page import PageMethod


class MobileBgSpider(scrapy.Spider):
    name = "mobile_bg"
    allowed_domains = ["mobile.bg"]
    source_id = "mobile_bg"
    
    custom_settings = {
        "CONCURRENT_REQUESTS": 2,
        "DOWNLOAD_DELAY": 1.0,
        "ROBOTSTXT_OBEY": True,
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
    }
    
    def start_requests(self):
        """Start scraping latest car listings"""
        # Start with cars page, sorted by newest
        base_url = "https://www.mobile.bg/pcgi/mobile.cgi?act=3&slink=tkqnfd"
        
        # Can add parameters for different pages
        for page_num in range(1, 6):  # First 5 pages
            url = f"{base_url}&f1={page_num}"
            yield scrapy.Request(
                url,
                callback=self.parse_listing_page,
                meta=dict(
                    playwright=True,
                    playwright_page_methods=[
                        PageMethod("wait_for_selector", ".tablereset", timeout=10000),
                    ],
                ),
            )
    
    def parse_listing_page(self, response):
        """Parse listing results page"""
        # Extract individual listing links
        listing_links = response.css('table.tablereset a.mmm::attr(href)').getall()
        
        for link in listing_links:
            if 'adv.php' in link:
                full_url = response.urljoin(link)
                yield scrapy.Request(
                    full_url,
                    callback=self.parse_listing_detail,
                    meta=dict(
                        playwright=True,
                        playwright_page_methods=[
                            PageMethod("wait_for_selector", ".announcement", timeout=10000),
                        ],
                    ),
                )
    
    def parse_listing_detail(self, response):
        """Parse individual listing detail page"""
        # Extract site_ad_id from URL
        site_ad_id_match = re.search(r'adv\.php.*?adv=(\d+)', response.url)
        site_ad_id = site_ad_id_match.group(1) if site_ad_id_match else None
        
        if not site_ad_id:
            self.logger.warning(f"Could not extract ad ID from {response.url}")
            return
        
        # Extract fields
        announcement = response.css('.announcement')
        
        # Brand and model
        title_full = response.css('h1::text').get() or ''
        title_parts = title_full.split()
        brand = title_parts[0] if len(title_parts) > 0 else None
        model = ' '.join(title_parts[1:3]) if len(title_parts) > 1 else None
        
        # Price
        price_text = response.css('.price::text').get() or ''
        price_match = re.search(r'([\d\s]+)', price_text.replace(' ', ''))
        price = int(price_match.group(1)) if price_match else None
        currency = 'BGN' if 'лв' in price_text else 'EUR'
        
        # Year
        year_match = re.search(r'(\d{4})\s*г', response.text)
        year = int(year_match.group(1)) if year_match else None
        
        # Mileage
        mileage_match = re.search(r'(\d+)\s*км', response.text)
        mileage_km = int(mileage_match.group(1)) if mileage_match else None
        
        # Fuel type
        fuel = None
        if 'Дизел' in response.text:
            fuel = 'diesel'
        elif 'Бензин' in response.text:
            fuel = 'petrol'
        elif 'Газ' in response.text:
            fuel = 'gas'
        elif 'Електро' in response.text:
            fuel = 'electric'
        elif 'Хибрид' in response.text:
            fuel = 'hybrid'
        
        # Gearbox
        gearbox = None
        if 'Автоматична' in response.text:
            gearbox = 'automatic'
        elif 'Ръчна' in response.text:
            gearbox = 'manual'
        
        # Description
        description = response.css('.description::text').get() or ''
        description = description.strip()
        
        # Images
        images = response.css('.car-image img::attr(src)').getall()
        
        # Phone
        phone_text = response.css('.phone::text').get() or ''
        phone_hash = hashlib.sha256(phone_text.encode()).hexdigest() if phone_text else None
        
        # Region
        region_text = response.css('.region::text').get() or ''
        region = region_text.strip() if region_text else None
        
        # Save raw HTML path (would be S3 in production)
        raw_html_path = f"raw/{self.source_id}/{site_ad_id}.html"
        
        yield {
            'listing_id': str(uuid4()),
            'source_id': self.source_id,
            'site_ad_id': site_ad_id,
            'url': response.url,
            'raw_html_path': raw_html_path,
            'raw_html': response.text,  # In production, upload to S3
            
            # Parsed fields
            'brand': brand,
            'model': model,
            'year': year,
            'mileage_km': mileage_km,
            'fuel': fuel,
            'gearbox': gearbox,
            'price': price,
            'currency': currency,
            'region': region,
            'title': title_full,
            'description': description,
            'images': images,
            'phone_hash': phone_hash,
            
            'first_seen_at': datetime.utcnow().isoformat(),
            'last_seen_at': datetime.utcnow().isoformat(),
            'is_active': True,
        }
