"""
Mobile.bg spider
"""
import re
import hashlib
from datetime import datetime
from uuid import uuid4

import scrapy


class MobileBgSpider(scrapy.Spider):
    name = "mobile_bg"
    allowed_domains = ["mobile.bg"]
    source_id = "mobile_bg"
    
    custom_settings = {
        "CONCURRENT_REQUESTS": 1,  # Very slow, respectful
        "DOWNLOAD_DELAY": 3.0,  # 3 second delay between requests
        "ROBOTSTXT_OBEY": False,
        "COOKIES_ENABLED": True,
        "RETRY_TIMES": 3,
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 429],
        # Rotate user agents
        "DOWNLOADER_MIDDLEWARES": {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
        },
        # Add random delays
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 3,
        "AUTOTHROTTLE_MAX_DELAY": 10,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0,
    }
    
    def start_requests(self):
        """Start scraping latest car listings"""
        # Try mobile version first - simpler HTML, less JavaScript
        # Or try direct listing URLs from API endpoints
        
        # Option 1: Mobile site (often simpler)
        base_url = "https://m.mobile.bg/obiavi/avtomobili-dzhipove"
        
        # Option 2: Try their internal API (often JSON, no HTML parsing needed)
        # api_url = "https://www.mobile.bg/api/search/ads"
        
        yield scrapy.Request(
            base_url,
            callback=self.parse_search_page,
            dont_filter=True,
            errback=self.errback_listing,
            headers={
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'bg-BG,bg;q=0.9',
            }
        )
    
    def parse_search_page(self, response):
        """Parse search results to find listing URLs"""
        self.logger.info(f"Parsing search page, response length: {len(response.text)}")
        
        # Try to find listing links
        # Mobile.bg uses various patterns for links
        links = response.css('a::attr(href)').getall()
        
        listing_count = 0
        for link in links:
            # Look for advertisement detail pages
            if 'adv.php' in link or 'adverts' in link:
                full_url = response.urljoin(link)
                self.logger.info(f"Found listing URL: {full_url}")
                listing_count += 1
                
                yield scrapy.Request(
                    full_url,
                    callback=self.parse_listing_detail,
                    dont_filter=True,
                    errback=self.errback_listing,
                )
                
                # Limit for testing
                if listing_count >= 3:
                    break
        
        if listing_count == 0:
            self.logger.warning(f"No listing links found on {response.url}")
            # Log first 500 chars of response for debugging
            self.logger.debug(f"Response preview: {response.text[:500]}")
    
    def errback_listing(self, failure):
        """Handle request failures"""
        self.logger.warning(f"Request failed: {failure.request.url} - {failure.value}")
    
    def parse_listing_detail(self, response):
        """Parse individual listing detail page (JSON API response)"""
        import json
        
        # Try parsing as JSON first (API endpoint)
        try:
            data = json.loads(response.text)
            
            # Extract data from JSON response
            site_ad_id = str(data.get('id', ''))
            if not site_ad_id:
                self.logger.warning(f"No ID in JSON response from {response.url}")
                return
            
            # Map JSON fields to our schema
            brand = data.get('make', '')
            model = data.get('model', '')
            year = data.get('year')
            mileage_km = data.get('mileage')
            price = data.get('price')
            currency = data.get('currency', 'BGN')
            
            # Fuel type mapping
            fuel_map = {
                'diesel': 'diesel',
                'petrol': 'petrol', 
                'gasoline': 'petrol',
                'electric': 'electric',
                'hybrid': 'hybrid',
                'lpg': 'gas',
            }
            fuel_raw = str(data.get('fuel', '')).lower()
            fuel = fuel_map.get(fuel_raw, fuel_raw if fuel_raw else None)
            
            # Gearbox
            gearbox_map = {
                'automatic': 'automatic',
                'manual': 'manual',
                'semi-automatic': 'automatic',
            }
            gearbox_raw = str(data.get('transmission', '')).lower()
            gearbox = gearbox_map.get(gearbox_raw, gearbox_raw if gearbox_raw else None)
            
            description = data.get('description', '')
            images = data.get('images', [])
            if isinstance(images, list):
                images = [img.get('url', img) if isinstance(img, dict) else img for img in images]
            
            # Phone hash
            phone = data.get('phone', '')
            phone_hash = hashlib.sha256(str(phone).encode()).hexdigest() if phone else None
            
            region = data.get('location', {}).get('city', '') if isinstance(data.get('location'), dict) else ''
            
            title = f"{brand} {model} {year}" if all([brand, model, year]) else data.get('title', '')
            
        except json.JSONDecodeError:
            # Fall back to HTML parsing
            self.logger.info(f"Not JSON, parsing HTML from {response.url}")
            
            # Extract site_ad_id from URL
            site_ad_id_match = re.search(r'(?:adv\.php.*?adv=|klasifieds/)(\d+)', response.url)
            site_ad_id = site_ad_id_match.group(1) if site_ad_id_match else None
            
            if not site_ad_id:
                self.logger.warning(f"Could not extract ad ID from {response.url}")
                return
            
            # HTML extraction (original logic)
            title_full = response.css('h1::text').get() or response.css('title::text').get() or ''
            title_parts = title_full.split()
            brand = title_parts[0] if len(title_parts) > 0 else None
            model = ' '.join(title_parts[1:3]) if len(title_parts) > 1 else None
            
            price_text = response.css('.price::text, .ad-price::text').get() or ''
            price_match = re.search(r'([\d\s]+)', price_text.replace(' ', ''))
            price = int(price_match.group(1)) if price_match else None
            currency = 'BGN' if 'лв' in price_text else 'EUR' if '€' in price_text else 'BGN'
            
            year_match = re.search(r'(\d{4})\s*г', response.text)
            year = int(year_match.group(1)) if year_match else None
            
            mileage_match = re.search(r'(\d+)\s*км', response.text)
            mileage_km = int(mileage_match.group(1)) if mileage_match else None
            
            fuel = None
            if 'Дизел' in response.text:
                fuel = 'diesel'
            elif 'Бензин' in response.text:
                fuel = 'petrol'
            elif 'Газ' in response.text or 'ГАЗ' in response.text:
                fuel = 'gas'
            elif 'Електро' in response.text:
                fuel = 'electric'
            elif 'Хибрид' in response.text:
                fuel = 'hybrid'
            
            gearbox = None
            if 'Автоматична' in response.text:
                gearbox = 'automatic'
            elif 'Ръчна' in response.text:
                gearbox = 'manual'
            
            description = response.css('.description::text, .ad-description::text').get() or ''
            description = description.strip()
            
            images = response.css('.car-image img::attr(src), .ad-photos img::attr(src)').getall()
            
            phone_text = response.css('.phone::text, .ad-phone::text').get() or ''
            phone_hash = hashlib.sha256(phone_text.encode()).hexdigest() if phone_text else None
            
            region_text = response.css('.region::text, .ad-location::text').get() or ''
            region = region_text.strip() if region_text else None
            
            title = title_full
        
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
