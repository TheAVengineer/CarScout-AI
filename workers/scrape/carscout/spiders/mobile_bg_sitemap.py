"""
Mobile.bg Sitemap Spider - Crawl from sitemaps (best approach!)
"""
import re
import json
import hashlib
from datetime import datetime
from uuid import uuid4

import scrapy
from scrapy.spiders import SitemapSpider


class MobileBgSitemapSpider(SitemapSpider):
    name = "mobile_bg_sitemap"
    allowed_domains = ["mobile.bg"]
    source_id = "mobile_bg"
    
    # Start with sitemap index
    sitemap_urls = ['https://www.mobile.bg/sitemap/index.xml']
    
    # Rules for which sitemaps to follow
    sitemap_rules = [
        # Match listing URLs: /obiava-{id}-{description}
        (r'/obiava-\d+', 'parse_listing_detail'),
    ]
    
    custom_settings = {
        "CONCURRENT_REQUESTS": 3,
        "DOWNLOAD_DELAY": 0.5,  # Can be faster with sitemaps
        "ROBOTSTXT_OBEY": True,
        "COOKIES_ENABLED": True,
        # Handle gzipped sitemaps
        "COMPRESSION_ENABLED": True,
    }
    
    def parse_listing_detail(self, response):
        """Parse individual listing detail page from sitemap"""
        import json
        
        # Extract listing ID from URL
        # Mobile.bg URLs: https://www.mobile.bg/obiava-11290002907403832-renault-clio-benzin-dizel
        site_ad_id_match = re.search(r'/obiava-(\d+)', response.url)
        if not site_ad_id_match:
            self.logger.warning(f"Could not extract ad ID from {response.url}")
            return
        
        site_ad_id = site_ad_id_match.group(1)
        
        # Try to find JSON-LD structured data first (common on listing sites)
        json_ld = response.css('script[type="application/ld+json"]::text').get()
        
        parsed_data = {}
        
        if json_ld:
            try:
                data = json.loads(json_ld)
                self.logger.info(f"Found JSON-LD data for {site_ad_id}")
                
                # Extract from structured data
                if isinstance(data, dict):
                    parsed_data['title'] = data.get('name', '')
                    parsed_data['description'] = data.get('description', '')
                    parsed_data['price'] = data.get('offers', {}).get('price')
                    parsed_data['currency'] = data.get('offers', {}).get('priceCurrency', 'BGN')
                    parsed_data['images'] = data.get('image', [])
                    if isinstance(parsed_data['images'], str):
                        parsed_data['images'] = [parsed_data['images']]
                    
            except json.JSONDecodeError:
                self.logger.warning(f"Failed to parse JSON-LD for {site_ad_id}")
        
        # Fall back to HTML parsing
        if not parsed_data.get('title'):
            # Extract title
            title = response.css('h1::text, .adPage__header__title::text').get() or ''
            title = title.strip()
            parsed_data['title'] = title
            
            # Try to extract brand and model from title
            title_parts = title.split()
            parsed_data['brand'] = title_parts[0] if len(title_parts) > 0 else None
            parsed_data['model'] = ' '.join(title_parts[1:3]) if len(title_parts) > 1 else None
        
        # Price extraction
        if not parsed_data.get('price'):
            price_text = response.css('.price::text, .adPage__price::text, [class*="price"]::text').get() or ''
            price_match = re.search(r'([\d\s]+)\s*(лв|EUR|€)', price_text)
            if price_match:
                parsed_data['price'] = int(price_match.group(1).replace(' ', ''))
                currency_text = price_match.group(2)
                parsed_data['currency'] = 'EUR' if currency_text in ['EUR', '€'] else 'BGN'
        
        # Year
        year_match = re.search(r'(\d{4})\s*г', response.text)
        parsed_data['year'] = int(year_match.group(1)) if year_match else None
        
        # Mileage
        mileage_match = re.search(r'(\d+)\s*км', response.text)
        parsed_data['mileage_km'] = int(mileage_match.group(1)) if mileage_match else None
        
        # Fuel type (Bulgarian text)
        fuel_mapping = {
            'Дизел': 'diesel',
            'Бензин': 'petrol',
            'Газ': 'gas',
            'ГАЗ': 'gas',
            'Електро': 'electric',
            'Хибрид': 'hybrid',
        }
        fuel = None
        for bg_fuel, en_fuel in fuel_mapping.items():
            if bg_fuel in response.text:
                fuel = en_fuel
                break
        parsed_data['fuel'] = fuel
        
        # Gearbox
        gearbox = None
        if 'Автоматична' in response.text:
            gearbox = 'automatic'
        elif 'Ръчна' in response.text:
            gearbox = 'manual'
        parsed_data['gearbox'] = gearbox
        
        # Description
        if not parsed_data.get('description'):
            desc = response.css('.description::text, .adPage__content__description::text, [class*="description"]::text').get() or ''
            parsed_data['description'] = desc.strip()
        
        # Images
        if not parsed_data.get('images'):
            images = response.css('img[src*="pic"]::attr(src), .adPage__gallery img::attr(src)').getall()
            # Clean and deduplicate
            clean_images = []
            for img in images:
                if 'no-image' not in img and img not in clean_images:
                    if img.startswith('//'):
                        img = 'https:' + img
                    elif img.startswith('/'):
                        img = 'https://www.mobile.bg' + img
                    clean_images.append(img)
            parsed_data['images'] = clean_images
        
        # Phone (if visible)
        phone_text = response.css('.phone::text, .adPage__phone::text, [class*="phone"]::text').get() or ''
        phone_hash = hashlib.sha256(phone_text.encode()).hexdigest() if phone_text else None
        
        # Region
        region = response.css('.region::text, .adPage__location::text, [class*="location"]::text').get() or ''
        region = region.strip()
        
        # Build output
        yield {
            'listing_id': str(uuid4()),
            'source_id': self.source_id,
            'site_ad_id': site_ad_id,
            'url': response.url,
            'raw_html_path': f"raw/{self.source_id}/{site_ad_id}.html",
            'raw_html': response.text,
            
            # Parsed fields
            'brand': parsed_data.get('brand'),
            'model': parsed_data.get('model'),
            'year': parsed_data.get('year'),
            'mileage_km': parsed_data.get('mileage_km'),
            'fuel': parsed_data.get('fuel'),
            'gearbox': parsed_data.get('gearbox'),
            'price': parsed_data.get('price'),
            'currency': parsed_data.get('currency', 'BGN'),
            'region': region if region else None,
            'title': parsed_data.get('title', ''),
            'description': parsed_data.get('description', ''),
            'images': parsed_data.get('images', []),
            'phone_hash': phone_hash,
            
            'first_seen_at': datetime.utcnow().isoformat(),
            'last_seen_at': datetime.utcnow().isoformat(),
            'is_active': True,
        }
