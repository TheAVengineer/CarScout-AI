"""
Cars.bg spider for scraping car listings from the last 24 hours

URL structure:
- Search: https://www.cars.bg/carslist.php?subm=1&add_search=1&typeoffer=1&last=1&conditions%5B%5D=4&conditions%5B%5D=1
- Detail: https://www.cars.bg/offer/{offer_id}

Key parameters:
- last=1: Listings from last 24 hours (last 1 day)
- typeoffer=1: Sales offers
- conditions[]=4: Used cars
- conditions[]=1: New cars
"""
import re
import hashlib
from datetime import datetime
from uuid import uuid4
from urllib.parse import urljoin, parse_qs, urlparse

import scrapy
from scrapy.http import Request


class CarsBgSpider(scrapy.Spider):
    name = "cars_bg"
    allowed_domains = ["cars.bg"]
    source_id = "cars_bg"
    
    custom_settings = {
        "CONCURRENT_REQUESTS": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "DOWNLOAD_DELAY": 3.0,  # Be respectful
        "ROBOTSTXT_OBEY": False,
        "COOKIES_ENABLED": True,
        "RETRY_TIMES": 3,
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 429],
        "DOWNLOAD_TIMEOUT": 30,
        "CLOSESPIDER_TIMEOUT": 0,
        # User agent
        "USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # AutoThrottle
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 3.0,
        "AUTOTHROTTLE_MAX_DELAY": 10.0,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 2.0,
    }
    
    def __init__(self, *args, **kwargs):
        """Initialize spider"""
        super().__init__(*args, **kwargs)
        
        # Tracking
        self.pages_scraped = 0
        self.items_scraped = 0
        self.last_scrape_time = None
        
        # Target listings (optional limit)
        self.target_listings = None
        if 'target_listings' in kwargs:
            try:
                self.target_listings = int(kwargs['target_listings'])
                self.logger.info(f"🎯 Target: {self.target_listings} listings")
            except ValueError:
                self.logger.warning(f"Invalid target_listings: {kwargs['target_listings']}")
        
        # Base search URL (last 1 day, new + used cars)
        self.base_url = "https://www.cars.bg/carslist.php?subm=1&add_search=1&typeoffer=1&last=1&conditions%5B%5D=4&conditions%5B%5D=1"
        
        self.logger.info("=" * 80)
        self.logger.info("🚗 Cars.bg Spider Starting")
        self.logger.info(f"📍 Source: {self.source_id}")
        self.logger.info(f"⏰ Scraping: Last 24 hours")
        if self.target_listings:
            self.logger.info(f"🎯 Target: {self.target_listings} listings")
        else:
            self.logger.info(f"🎯 Target: ALL listings (continuous)")
        self.logger.info("=" * 80)
    
    def start_requests(self):
        """Start scraping from the first page"""
        yield Request(
            url=self.base_url,
            callback=self.parse_listing_page,
            meta={
                "playwright": False,  # No need for Playwright, regular requests work
                "page_num": 1
            },
            dont_filter=True  # Always fetch the first page
        )
    
    def parse_listing_page(self, response):
        """Parse a search results page and extract listing URLs"""
        page_num = response.meta.get('page_num', 1)
        self.logger.info(f"📄 Parsing page {page_num}: {response.url}")
        
        # Extract listing URLs
        # Cars.bg uses full URLs: <a href="https://www.cars.bg/offer/{offer_id}">
        listing_links = response.css('a[href*="cars.bg/offer/"]::attr(href)').getall()
        
        if not listing_links:
            # Try alternative selector (relative paths)
            listing_links = response.css('a[href^="/offer/"]::attr(href)').getall()
        
        self.logger.info(f"🔍 Found {len(listing_links)} listings on page {page_num}")
        
        if not listing_links:
            self.logger.warning(f"⚠️ No listings found on page {page_num}")
            # Try to extract and log page content for debugging
            self.logger.debug(f"Page title: {response.css('title::text').get()}")
            self.logger.debug(f"First 500 chars: {response.text[:500]}")
        
        # Deduplicate URLs (same listing can appear multiple times)
        seen_urls = set()
        unique_links = []
        for link in listing_links:
            full_url = response.urljoin(link)
            if full_url not in seen_urls:
                seen_urls.add(full_url)
                unique_links.append(full_url)
        
        self.logger.info(f"✨ Unique listings: {len(unique_links)}")
        
        # Extract each listing
        for listing_url in unique_links:
            # Check if we've reached the target
            if self.target_listings and self.items_scraped >= self.target_listings:
                self.logger.info(f"🎯 Target reached: {self.items_scraped}/{self.target_listings}")
                return
            
            yield Request(
                url=listing_url,
                callback=self.parse_listing,
                meta={
                    "page_num": page_num,
                    "playwright": False
                },
                errback=self.handle_error
            )
        
        # Check for next page
        # Cars.bg uses pagination links like: ?page=2, ?page=3, etc.
        next_page_links = response.css('a[href*="page="]::attr(href)').getall()
        
        if next_page_links:
            # Find the highest page number
            page_numbers = []
            for link in next_page_links:
                match = re.search(r'page=(\d+)', link)
                if match:
                    page_numbers.append(int(match.group(1)))
            
            if page_numbers:
                next_page = max(page_numbers)
                if next_page > page_num:
                    # Check if we should continue
                    if not self.target_listings or self.items_scraped < self.target_listings:
                        next_url = f"{self.base_url}&page={next_page}"
                        self.logger.info(f"➡️ Next page: {next_page}")
                        
                        yield Request(
                            url=next_url,
                            callback=self.parse_listing_page,
                            meta={
                                "playwright": False,
                                "page_num": next_page
                            },
                            dont_filter=True
                        )
                    else:
                        self.logger.info(f"🎯 Target reached, stopping pagination")
                else:
                    self.logger.info(f"📊 Last page reached (page {page_num})")
        else:
            self.logger.info(f"📊 No more pages (page {page_num})")
        
        self.pages_scraped += 1
    
    def parse_listing(self, response):
        """Parse a single listing detail page"""
        self.logger.info(f"🔎 Parsing listing: {response.url}")
        
        # Extract offer ID from URL: /offer/{offer_id}
        offer_id_match = re.search(r'/offer/([a-f0-9]+)', response.url)
        site_ad_id = offer_id_match.group(1) if offer_id_match else None
        
        if not site_ad_id:
            self.logger.warning(f"⚠️ Could not extract offer ID from {response.url}")
            return
        
        # Generate listing hash
        listing_hash = hashlib.md5(f"cars_bg_{site_ad_id}".encode()).hexdigest()
        
        # Extract title from multiple sources
        # Priority: h2 > title tag
        title = response.css('h2::text').get()
        
        # Also extract from title tag for price and other info
        page_title = response.css('title::text').get()
        
        if not title and page_title:
            # Format: "CARS.BG - Ford Focus 2.0 TDC/ 150к.с, 14490 BGN, Дизел"
            if 'CARS.BG' in page_title:
                title = page_title.replace('CARS.BG - ', '').split(',')[0].strip()
        
        title = title.strip() if title else ""
        
        # Parse brand and model from title
        brand, model = self._extract_brand_model(title)
        
        # Extract the details paragraph
        # Format: "Март 2016, Хечбек, Употребяван автомобил, В добро състояние, Дизел, 185 000км, Ръчни скорости, 150к.с., EURO 6, 2000см3, 4/5 врати, Червен"
        details_text = response.css('.text-copy::text').get()
        if not details_text:
            # Try to find it in any paragraph near the title
            details_text = ' '.join(response.css('p::text').getall())
        
        # Clean the details text
        details_text = details_text.strip() if details_text else ""
        details_text = details_text.replace('\n', ' ').replace('\r', ' ')
        details_text = re.sub(r'\s+', ' ', details_text)  # Collapse multiple spaces
        
        # Extract price from title tag (most reliable source)
        # Format: "CARS.BG - Ford Focus 2.0 TDC/ 150к.с, 14490 BGN, Дизел"
        price = None
        currency = "BGN"
        
        if page_title:
            # Try to find price in title tag
            bgn_match = re.search(r'(\d[\d\s,]*)\s*BGN', page_title)
            eur_match = re.search(r'(\d[\d\s,\.]*)\s*EUR', page_title)
            
            if bgn_match:
                price = self._extract_price(bgn_match.group(1))
                currency = "BGN"
            elif eur_match:
                price = self._extract_price(eur_match.group(1))
                currency = "EUR"
        
        # Fallback: try to find price in page body
        if not price:
            price_texts = response.css('[class*="price"]::text').getall()
            price_string = ' '.join(price_texts)
            
            bgn_match = re.search(r'(\d[\d\s,]*)\s*BGN', price_string)
            eur_match = re.search(r'(\d[\d\s,\.]*)\s*EUR', price_string)
            
            if bgn_match:
                price = self._extract_price(bgn_match.group(1))
                currency = "BGN"
            elif eur_match:
                price = self._extract_price(eur_match.group(1))
                currency = "EUR"
        
        # Parse details from the paragraph
        # Extract year (Март 2016 = March 2016)
        # Bulgarian month names
        bulgarian_months = {
            'Януари': '01', 'Февруари': '02', 'Март': '03', 'Април': '04',
            'Май': '05', 'Юни': '06', 'Юли': '07', 'Август': '08',
            'Септември': '09', 'Октомври': '10', 'Ноември': '11', 'Декември': '12'
        }
        
        year = None
        # Try month + year format first
        for month_name in bulgarian_months:
            if month_name in details_text:
                year_match = re.search(f'{month_name}\\s+(\\d{{4}})', details_text)
                if year_match:
                    year = int(year_match.group(1))
                    break
        
        # If not found, try standalone year
        if not year:
            year_match = re.search(r'\b(19|20)\d{2}\b', details_text)
            year = int(year_match.group(0)) if year_match else None
        
        # Extract mileage (185 000км)
        mileage_match = re.search(r'(\d[\d\s]*)\s*км', details_text, re.IGNORECASE)
        mileage = self._extract_mileage(mileage_match.group(1)) if mileage_match else None
        
        # Extract fuel type (Дизел, Бензин, etc.)
        fuel_type = None
        if 'Дизел' in details_text:
            fuel_type = 'Diesel'
        elif 'Бензин' in details_text:
            fuel_type = 'Petrol'
        elif 'Газ' in details_text or 'ГАЗ' in details_text:
            fuel_type = 'LPG/CNG'
        elif 'Електро' in details_text:
            fuel_type = 'Electric'
        elif 'Хибрид' in details_text:
            fuel_type = 'Hybrid'
        
        # Extract transmission (Ръчни скорости = Manual, Автоматични = Automatic)
        transmission = None
        if 'Автоматични' in details_text:
            transmission = 'Automatic'
        elif 'Ръчни' in details_text:
            transmission = 'Manual'
        
        # Extract power (150к.с.)
        power_match = re.search(r'(\d+)\s*к\.с\.', details_text)
        power = int(power_match.group(1)) if power_match else None
        
        # Extract engine size (2000см3)
        engine_match = re.search(r'(\d+)\s*см3', details_text)
        engine_size = int(engine_match.group(1)) if engine_match else None
        
        # Extract color (last word usually, e.g., "Червен" = Red)
        color_match = re.search(r',\s*([А-Яа-я]+)\s*$', details_text)
        color = color_match.group(1) if color_match else None
        
        # Extract body type (Хечбек, Купе, Седан, etc.)
        body_type = None
        if 'Хечбек' in details_text:
            body_type = 'Hatchback'
        elif 'Седан' in details_text:
            body_type = 'Sedan'
        elif 'Комби' in details_text or 'Стейшън' in details_text:
            body_type = 'Estate'
        elif 'Купе' in details_text:
            body_type = 'Coupe'
        elif 'Джип' in details_text or 'SUV' in details_text:
            body_type = 'SUV'
        elif 'Ван' in details_text or 'Миниван' in details_text:
            body_type = 'Van'
        elif 'Кабрио' in details_text:
            body_type = 'Convertible'
        
        # Extract condition (Употребяван = Used, Нов = New)
        condition = 'Used'
        if 'Нов автомобил' in details_text:
            condition = 'New'
        
        # Extract location
        # Usually appears after seller info
        location_candidates = response.css('[class*="location"]::text, td:contains("София")::text, td:contains("Пловдив")::text').getall()
        location = None
        for loc in location_candidates:
            loc = loc.strip()
            if loc and len(loc) > 2 and not any(char.isdigit() for char in loc):
                location = loc
                break
        
        # If not found, try common city names in the page text
        page_text = ' '.join(response.css('body *::text').getall())
        for city in ['София', 'Пловдив', 'Варна', 'Бургас', 'Русе', 'Стара Загора', 'Плевен', 'Благоевград']:
            if city in page_text and not location:
                location = city
                break
        
        # Extract seller info
        seller_text = response.css('td:contains("Частно лице")::text, td:contains("Фирма")::text').get()
        is_dealer = seller_text and 'Фирма' in seller_text or 'ООД' in page_text or 'ЕООД' in page_text
        seller_name = None
        if not is_dealer:
            # Try to find seller name
            seller_name_match = response.css('[class*="seller"]::text, td:contains("Продавач")::text').get()
            if seller_name_match:
                seller_name = seller_name_match.strip()
        
        # Extract description
        # The description is usually in the text-copy div or after the details
        description_parts = response.css('.text-copy::text').getall()
        # Skip the first part (that's the details), get the rest
        if len(description_parts) > 1:
            description = ' '.join(p.strip() for p in description_parts[1:] if p.strip())
        else:
            description = details_text
        
        # Extract images
        # Cars.bg uses: https://g1-bg.cars.bg/2025-10-16_1/68f0a83d6de3c97b7202f3f3o.jpg
        image_urls = response.css('img[src*="g1-bg.cars.bg"]::attr(src), img[src*="cars.bg"]::attr(src)').getall()
        # Filter to only actual car images (not icons/logos)
        image_urls = [url for url in image_urls if '/2' in url and 'http' in url]  # Year pattern in path
        # Remove duplicates
        image_urls = list(dict.fromkeys(image_urls))
        
        # Extract phone number (if visible)
        # Cars.bg may show phone like: 0878129005
        phone_text = response.css('a[href^="tel:"]::attr(href)').get()
        phone_hash = None
        if phone_text:
            phone_number = phone_text.replace('tel:', '').replace('+359', '0').strip()
            phone_hash = hashlib.md5(phone_number.encode()).hexdigest()
        
        # Generate seller hash
        seller_identifier = seller_name or location or phone_hash or "unknown"
        seller_hash = hashlib.md5(f"cars_bg_{seller_identifier}".encode()).hexdigest()
        
        # Build the listing item
        item = {
            "listing_id": str(uuid4()),
            "listing_hash": listing_hash,
            "source_id": self.source_id,  # Changed from "source" to match pipeline expectations
            "url": response.url,  # Changed from "source_url" to match pipeline expectations
            "site_ad_id": site_ad_id,
            
            # Car details
            "brand": brand,
            "model": model,
            "year": year,
            "price": price,
            "currency": currency,
            "mileage_km": mileage,
            "fuel_type": fuel_type,
            "transmission": transmission,
            "power_hp": power,
            "engine_size_cc": engine_size,
            "color": color,
            "body_type": body_type,
            "condition": condition,
            
            # Additional details
            "title": title,
            "description": description,
            "location": location,
            "image_urls": image_urls,
            
            # Seller info
            "seller_name": seller_name,
            "seller_hash": seller_hash,
            "phone_hash": phone_hash,
            "is_dealer": is_dealer,
            
            # Metadata
            "scraped_at": datetime.now().isoformat(),
            "page_num": response.meta.get('page_num', 1),
        }
        
        # Log success
        self.items_scraped += 1
        self.last_scrape_time = datetime.now()
        
        self.logger.info(
            f"✅ Scraped: {brand} {model} {year} - "
            f"{price} {currency}"
        )
        
        yield item
    
    def _extract_brand_model(self, title):
        """Extract brand and model from title
        
        Cars.bg title format: "CARS.BG - Brand Model Details, Price BGN, ..."
        Example: "CARS.BG - Peugeot 308 HDI/USB/NAVI, 15900 BGN, Дизел"
        """
        if not title:
            return None, None
        
        # Remove "CARS.BG - " prefix if present
        if 'CARS.BG' in title:
            title = re.sub(r'CARS\.BG\s*-\s*', '', title, flags=re.IGNORECASE)
        
        # Common brand patterns
        brands = [
            'Mercedes-Benz', 'Mercedes',  # Mercedes-Benz must come before Mercedes
            'Alfa Romeo', 'Land Rover', 'Range Rover', 'Rolls-Royce',  # Multi-word brands first
            'Audi', 'BMW', 'VW', 'Volkswagen',
            'Opel', 'Ford', 'Toyota', 'Renault', 'Peugeot', 'Citroën', 'Citroen',
            'Mazda', 'Nissan', 'Honda', 'Hyundai', 'Kia', 'Škoda', 'Skoda',
            'Seat', 'Fiat', 'Dacia', 'Suzuki', 'Mitsubishi',
            'Subaru', 'Volvo', 'Lexus', 'Infiniti', 'Porsche',
            'Jaguar', 'Mini', 'Smart', 'Jeep', 'Chevrolet',
            'Dodge', 'Chrysler', 'Cadillac', 'Tesla', 'Bentley'
        ]
        
        brand = None
        model = None
        
        # Find brand (check multi-word brands first)
        title_upper = title.upper()
        for b in brands:
            if b.upper() in title_upper:
                brand = b
                break
        
        if brand:
            # Extract model from Cars.bg format
            # After brand, model is everything until: comma, price (digit followed by BGN/EUR), or EOL
            brand_pos = title_upper.find(brand.upper())
            after_brand = title[brand_pos + len(brand):].strip()
            
            # Model extraction: stop at comma OR price pattern (e.g., "15900 BGN")
            # Allow alphanumeric, spaces, slashes, dashes in model name
            model_match = re.match(r'^([A-Za-z0-9\-\s/\.]+?)(?:\s*,|\s+\d+\s*(?:BGN|EUR)|$)', after_brand, re.IGNORECASE)
            if model_match:
                model_raw = model_match.group(1).strip()
                # Clean up model: keep first 2-3 words/numbers (e.g., "308 HDI" or "C 220 CDI")
                # This removes excessive details like "HDI/USB/NAVI"
                model_parts = re.findall(r'\S+', model_raw)
                if model_parts:
                    # Take first 3 parts or until we hit very long descriptive text
                    model = ' '.join(model_parts[:3]) if len(model_parts) > 3 else model_raw
                    # Remove trailing slashes or dots
                    model = re.sub(r'[/\.\-]+$', '', model).strip()
        
        return brand, model
    
    def _extract_price(self, price_text):
        """Extract numeric price from text"""
        if not price_text:
            return None
        
        # Remove all non-numeric characters except decimal point
        # Handle formats: "23,500", "12,015.36", "23 500", "14490"
        price_clean = re.sub(r'[^\d\.]', '', price_text)
        
        try:
            return float(price_clean)
        except ValueError:
            return None
    
    def _extract_currency(self, price_text):
        """Extract currency from price text"""
        if not price_text:
            return "BGN"
        
        text_upper = price_text.upper()
        if 'EUR' in text_upper or '€' in text_upper:
            return "EUR"
        elif 'BGN' in text_upper or 'ЛВ' in text_upper:
            return "BGN"
        else:
            return "BGN"  # Default
    
    def _extract_mileage(self, mileage_text):
        """Extract numeric mileage from text"""
        if not mileage_text:
            return None
        
        # Remove non-numeric characters
        mileage_clean = re.sub(r'[^\d]', '', mileage_text)
        
        try:
            return int(mileage_clean)
        except ValueError:
            return None
    
    def _normalize_fuel(self, fuel_text):
        """Normalize fuel type to standard values"""
        if not fuel_text:
            return None
        
        text_upper = fuel_text.upper()
        
        if 'ДИЗЕЛ' in text_upper or 'DIESEL' in text_upper:
            return 'Diesel'
        elif 'БЕНЗИН' in text_upper or 'PETROL' in text_upper or 'GASOLINE' in text_upper:
            return 'Petrol'
        elif 'ГАЗ' in text_upper or 'LPG' in text_upper or 'CNG' in text_upper:
            return 'LPG/CNG'
        elif 'ЕЛЕКТРО' in text_upper or 'ELECTRIC' in text_upper:
            return 'Electric'
        elif 'ХИБРИД' in text_upper or 'HYBRID' in text_upper:
            return 'Hybrid'
        else:
            return fuel_text  # Return original if can't normalize
    
    def handle_error(self, failure):
        """Handle request errors"""
        self.logger.error(f"❌ Request failed: {failure.request.url}")
        self.logger.error(f"   Error: {failure.value}")
    
    def closed(self, reason):
        """Called when spider closes"""
        self.logger.info("=" * 80)
        self.logger.info(f"🏁 Cars.bg Spider Finished")
        self.logger.info(f"📊 Stats:")
        self.logger.info(f"   Pages scraped: {self.pages_scraped}")
        self.logger.info(f"   Items scraped: {self.items_scraped}")
        self.logger.info(f"   Reason: {reason}")
        self.logger.info("=" * 80)
