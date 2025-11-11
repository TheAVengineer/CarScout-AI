"""
Mobile.bg Deal Monitor Spider

Purpose: Continuously monitor newest listings on Mobile.bg for fresh deals.
Instead of re-scraping everything, this spider:
1. Checks only newest listings (sort=6)
2. Detects new listings not in database
3. Applies pre-filters (price, mileage, year, etc.)
4. Evaluates with AI only promising listings
5. Posts good deals (score ≥7.5) to Telegram channel

This is much more efficient than bulk scraping!
"""

import scrapy
from datetime import datetime, timedelta
from pathlib import Path
import json
import os
from typing import Dict, Any, Optional


class MobileBgMonitorSpider(scrapy.Spider):
    """Monitor Mobile.bg for new deals in real-time"""
    
    name = "mobile_bg_monitor"
    allowed_domains = ["mobile.bg"]
    
    custom_settings = {
        # Monitor mode is FAST - we only check first few pages
        'CONCURRENT_REQUESTS': 4,
        'DOWNLOAD_DELAY': 1.0,  # Faster polling
        
        # Playwright for JavaScript rendering
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        
        # Use monitoring pipeline (different from bulk scraper)
        'ITEM_PIPELINES': {
            'carscout.pipelines_monitor.DealMonitorPipeline': 100,
        },
        
        # Abort unnecessary resources
        'PLAYWRIGHT_ABORT_REQUEST': lambda req: req.resource_type in ('image', 'stylesheet', 'font', 'media'),
        
        # Fast timeouts for monitoring
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 15000,  # 15s
        'DOWNLOAD_TIMEOUT': 20,
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Track processed listings in this run (prevent duplicates)
        self.seen_this_run = set()
        
        # Config will be loaded in start_requests where settings are available
        self.config = None
        
        # Set to store existing listing IDs from database (populated by pipeline)
        self.existing_listing_ids = set()
    
    def _load_monitor_config(self) -> Dict[str, Any]:
        """Load monitoring configuration from file"""
        # Check if custom config path is provided via Scrapy settings
        # Note: settings is available after from_crawler
        custom_config = getattr(self, 'settings', None) and self.settings.get('MONITOR_CONFIG_PATH')
        
        if custom_config:
            config_path = Path(custom_config)
            self.logger.info(f"📋 Using custom config: {config_path}")
        else:
            # Default to monitor_config.json in project root
            config_path = Path(__file__).resolve().parent.parent.parent.parent.parent / "monitor_config.json"
            self.logger.info(f"📋 Using default config: {config_path}")
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.logger.info(f"✅ Loaded {len(config.get('watch_targets', []))} targets from config")
                return config
        
        # Default configuration if file doesn't exist
        return {
            "watch_targets": [
                {
                    "name": "All New Cars",
                    "url": "https://www.mobile.bg/obiavi/avtomobili-dzhipove?sort=6",
                    "pages": 3,  # Check first 3 pages only
                    "filters": {
                        "price_max": 100000,
                        "year_min": 2015,
                        "mileage_max": 150000
                    }
                },
                {
                    "name": "Mercedes A-Class New",
                    "url": "https://www.mobile.bg/obiavi/avtomobili-dzhipove/mercedes-benz/a-klasa?sort=6",
                    "pages": 2,
                    "filters": {
                        "price_max": 50000,
                        "year_min": 2018,
                        "mileage_max": 100000
                    }
                },
                {
                    "name": "BMW 3 Series New",
                    "url": "https://www.mobile.bg/obiavi/avtomobili-dzhipove/bmw/3-seriya?sort=6",
                    "pages": 2,
                    "filters": {
                        "price_max": 60000,
                        "year_min": 2018,
                        "mileage_max": 120000
                    }
                }
            ],
            "ai_evaluation": {
                "enabled": True,
                "min_score_to_post": 7.5,
                "evaluate_all": False  # Only evaluate if passes pre-filters
            },
            "monitoring_interval": 300  # 5 minutes between runs
        }
    
    def start_requests(self):
        """Generate requests for all watch targets"""
        # Load config here where settings are available
        if self.config is None:
            self.config = self._load_monitor_config()
            self.logger.info(f"🔍 Monitor initialized with {len(self.config.get('watch_targets', []))} watch targets")
        
        for target in self.config.get('watch_targets', []):
            target_name = target.get('name', 'Unknown')
            base_url = target.get('url')
            pages_to_check = target.get('pages', 3)
            
            self.logger.info(f"🎯 Watching: {target_name} - {pages_to_check} pages")
            
            # First page
            yield scrapy.Request(
                url=base_url,
                callback=self.parse_listing_page,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_goto_kwargs': {
                        'wait_until': 'networkidle',
                        'timeout': 15000,
                    },
                    'target_config': target,
                    'page_num': 1,
                },
                errback=self.errback_close_page,
            )
    
    async def parse_listing_page(self, response):
        """Parse search results page for listing URLs"""
        page = response.meta["playwright_page"]
        target_config = response.meta['target_config']
        page_num = response.meta['page_num']
        target_name = target_config.get('name', 'Unknown')
        
        self.logger.info(f"📄 Parsing page {page_num} of {target_name}")
        
        # Wait for listing links to load (like main spider)
        try:
            await page.wait_for_selector('a[href*="/obiava-"]', timeout=10000)
        except Exception as e:
            self.logger.warning(f"⚠️ Timeout waiting for listings on page {page_num}: {e}")
            await page.close()
            return
        
        # Extract ALL links and filter for listings (like main spider)
        all_links = response.css('a::attr(href)').getall()
        listing_links = [link for link in all_links if self._is_listing_url(link)]
        
        if not listing_links:
            self.logger.warning(f"⚠️ No listings found on page {page_num}")
            await page.close()
            return
        
        self.logger.info(f"✅ Found {len(listing_links)} listings on page {page_num}")
        
        # Process each listing
        for link in listing_links:
            full_url = response.urljoin(link)
            
            # Extract listing ID from URL
            # Format: /obiava-XXXXXXXXXXX-brand-model
            listing_id = self._extract_listing_id(full_url)
            
            if not listing_id:
                continue
            
            # Skip if already seen in this run
            if listing_id in self.seen_this_run:
                continue
            
            # ✅ CRITICAL FIX: Skip if already in database!
            if listing_id in self.existing_listing_ids:
                # self.logger.debug(f"⏭️  Skipping {listing_id} - already in DB")
                continue
            
            self.seen_this_run.add(listing_id)
            self.logger.info(f"🆕 NEW listing found: {listing_id}")
            
            # Yield request to scrape detail page ONLY for NEW listings
            yield scrapy.Request(
                url=full_url,
                callback=self.parse_listing_detail,
                dont_filter=True,  # Force processing even if URL seen before
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_goto_kwargs': {
                        'wait_until': 'networkidle',
                        'timeout': 15000,
                    },
                    'listing_id': listing_id,
                    'target_config': target_config,
                },
                errback=self.errback_close_page,
            )
            self.logger.info(f"📤 Yielded detail page request for {listing_id}: {full_url}")
        
        # Check if we should scrape next page
        max_pages = target_config.get('pages', 3)
        if page_num < max_pages:
            # Find next page link
            next_page = response.css('a.pageNumbersA:contains("Напред")::attr(href)').get()
            if next_page:
                yield scrapy.Request(
                    url=response.urljoin(next_page),
                    callback=self.parse_listing_page,
                    meta={
                        'playwright': True,
                        'playwright_include_page': True,
                        'playwright_page_goto_kwargs': {
                            'wait_until': 'networkidle',
                            'timeout': 15000,
                        },
                        'target_config': target_config,
                        'page_num': page_num + 1,
                    },
                    errback=self.errback_close_page,
                )
        
        # Don't close page here - Scrapy-Playwright will handle it
        # If we close here, yielded requests won't be processed
    
    async def parse_listing_detail(self, response):
        """Parse individual listing detail page"""
        page = response.meta["playwright_page"]
        listing_id = response.meta['listing_id']
        target_config = response.meta['target_config']
        
        try:
            self.logger.info(f"🔍 Parsing listing: {listing_id}")
            
            # Extract all listing data (same as main spider)
            item = {
                'source': 'mobile.bg',
                'site_ad_id': listing_id,
                'url': response.url,
                'target_config': target_config,  # Pass filters to pipeline
                'scraped_at': datetime.now().isoformat(),
            }
            
            # Extract brand
            brand_elem = response.css('div.dilarData a[href*="/obiavi/avtomobili-dzhipove/"]::text').get()
            if brand_elem:
                item['brand'] = brand_elem.strip()
            
            # Extract model
            model_elem = response.css('div.dilarData a[href*="/obiavi/avtomobili-dzhipove/"]:nth-of-type(2)::text').get()
            if model_elem:
                item['model'] = model_elem.strip()
            
            # Extract price
            price_text = response.css('span.price::text').get()
            if price_text:
                # Remove spaces and "лв." suffix
                price_clean = price_text.strip().replace(' ', '').replace('лв.', '')
                try:
                    item['price'] = float(price_clean)
                    item['currency'] = 'BGN'
                except ValueError:
                    self.logger.warning(f"Could not parse price: {price_text}")
            
            # Extract year
            year_elem = response.xpath('//th[contains(text(), "Година")]/following-sibling::td/text()').get()
            if year_elem:
                try:
                    item['year'] = int(year_elem.strip())
                except ValueError:
                    pass
            
            # Extract mileage
            mileage_elem = response.xpath('//th[contains(text(), "Пробег")]/following-sibling::td/text()').get()
            if mileage_elem:
                # Format: "123 456 км"
                mileage_clean = mileage_elem.strip().replace(' ', '').replace('км', '')
                try:
                    item['mileage'] = int(mileage_clean)
                except ValueError:
                    pass
            
            # Extract power (PS)
            power_elem = response.xpath('//th[contains(text(), "Мощност")]/following-sibling::td/text()').get()
            if power_elem:
                # Format: "150 к.с."
                power_clean = power_elem.strip().replace(' ', '').replace('к.с.', '').replace('к.с', '')
                try:
                    item['power_ps'] = int(power_clean)
                except ValueError:
                    pass
            
            # Extract fuel type
            fuel_elem = response.xpath('//th[contains(text(), "Гориво")]/following-sibling::td/text()').get()
            if fuel_elem:
                item['fuel_type'] = fuel_elem.strip()
            
            # Extract transmission
            transmission_elem = response.xpath('//th[contains(text(), "Скоростна кутия")]/following-sibling::td/text()').get()
            if transmission_elem:
                item['transmission'] = transmission_elem.strip()
            
            # Extract body type
            body_elem = response.xpath('//th[contains(text(), "Категория")]/following-sibling::td/text()').get()
            if body_elem:
                item['body_type'] = body_elem.strip()
            
            # Extract description
            description_elem = response.css('div.description::text').getall()
            if description_elem:
                item['description'] = ' '.join([d.strip() for d in description_elem if d.strip()])
            
            # Extract images
            image_urls = response.css('div.pic a::attr(href)').getall()
            if image_urls:
                item['images'] = [response.urljoin(url) for url in image_urls]
            
            # Extract location
            location_elem = response.css('div.dilarData a[href*="/obiavi/avtomobili-dzhipove/grad-"]::text').get()
            if location_elem:
                item['location'] = location_elem.strip()
            
            # Extract seller phone hash (for deduplication)
            phone_elem = response.css('div.phone::text').get()
            if phone_elem:
                item['seller_phone'] = phone_elem.strip()
            
            self.logger.info(f"✅ Extracted: {item.get('brand')} {item.get('model')} {item.get('year')} - {item.get('price')} {item.get('currency')}")
            
            yield item
        
        finally:
            await page.close()
    
    def _is_listing_url(self, url: str) -> bool:
        """Check if URL is a car listing detail page (same logic as main spider)"""
        if not url:
            return False
        
        # Exclude non-listing pages
        if any(x in url.lower() for x in ['users', 'login', 'register', 'check-phone', 'javascript:', '#', '/p-', 'mailto:']):
            return False
        
        # Match Mobile.bg listing URL pattern: /obiava-XXXXXXXXXXXXXXXXX-...
        if '/obiava-' in url:
            try:
                id_part = url.split('/obiava-')[1].split('-')[0]
                # Check if it's a numeric ID (17-20 digits)
                if id_part.isdigit() and len(id_part) >= 17:
                    return True
            except Exception:
                pass
        
        return False
    
    def _extract_listing_id(self, url: str) -> Optional[str]:
        """Extract listing ID from Mobile.bg URL"""
        # Format: /obiava-XXXXXXXXXXX-brand-model
        try:
            parts = url.split('/')
            for part in parts:
                if part.startswith('obiava-'):
                    # Extract ID after 'obiava-' and before brand name
                    id_part = part.replace('obiava-', '').split('-')[0]
                    return id_part
        except Exception as e:
            self.logger.error(f"Error extracting listing ID from {url}: {e}")
        return None
    
    async def errback_close_page(self, failure):
        """Close page on error"""
        page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()
        self.logger.error(f"Request failed: {failure}")
