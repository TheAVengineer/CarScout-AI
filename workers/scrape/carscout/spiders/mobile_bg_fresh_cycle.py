"""
Mobile.bg Fresh Deals - Complete Cycle Spider

Runs ONE complete cycle through all brands:
1. Scrapes fresh listings (sort=7, last 2 days) for each brand
2. Seeds to database
3. Stops after completing all brands

Designed to be run via cronjob every 6 hours

Usage:
    scrapy crawl mobile_bg_fresh_cycle
"""

import scrapy
from typing import Iterator
from .mobile_bg import MobileBgSpider


class MobileBgFreshCycleSpider(MobileBgSpider):
    """One-cycle spider for fresh Mobile.bg listings
    
    Completes one full pass through all brands with sort=7 filter,
    then stops automatically.
    """
    
    name = "mobile_bg_fresh_cycle"
    
    # Brands to scrape (in priority order - most popular first)
    BRANDS = [
        'mercedes-benz',
        'bmw',
        'audi',
        'volkswagen',
        'opel',
        'ford',
        'toyota',
        'renault',
        'peugeot',
        'citroen',
        'skoda',
        'seat',
        'honda',
        'mazda',
        'nissan',
        'hyundai',
        'kia',
        'volvo',
        'fiat',
        'alfa-romeo',
    ]
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
        'DOWNLOAD_DELAY': 1.5,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 5,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 4.0,
        
        # Use the FAST pipeline (already handles parsing and database seeding)
        # The pipeline will trigger market-aware scoring via Celery tasks
        'ITEM_PIPELINES': {
            'carscout.pipelines_fast.FastCarScoutPipeline': 300,
        },
        
        # Stop after first idle period (all brands scraped)
        'CLOSESPIDER_TIMEOUT': 3600,  # Max 1 hour per cycle
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.total_brands = len(self.BRANDS)
        self.listings_found = 0
        self.start_time = None
    
    def start_requests(self) -> Iterator[scrapy.Request]:
        """Generate requests for all brands with sort=7"""
        from datetime import datetime
        self.start_time = datetime.now()
        
        self.logger.info("="*70)
        self.logger.info("🚀 STARTING FRESH DEALS CYCLE")
        self.logger.info(f"   Brands to scrape: {self.total_brands}")
        self.logger.info(f"   Filter: Last 2 days (sort=7)")
        self.logger.info(f"   Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("="*70)
        
        for brand in self.BRANDS:
            # Build search URL with sort=7 (last 2 days)
            # Using the working format: /namira-se-v-balgariya?sort=7
            search_url = f"https://www.mobile.bg/obiavi/avtomobili-dzhipove/{brand}/namira-se-v-balgariya?sort=7"
            
            self.logger.info(f"📋 Queuing brand: {brand}")
            
            yield scrapy.Request(
                url=search_url,
                callback=self.parse_search_page,
                meta={
                    'brand': brand,
                    'playwright': True,
                    'playwright_include_page': True,
                },
                errback=self.errback_listing,  # Use parent's error handler
            )
    
    async def parse_search_page(self, response):
        """Parse search results page AND handle pagination"""
        brand = response.meta.get('brand', 'unknown')
        page_number = response.meta.get('page_number', 1)
        
        # Wait for JavaScript to load listings
        playwright_page = response.meta.get("playwright_page")
        if playwright_page:
            try:
                await playwright_page.wait_for_selector('a[href*="/obiava-"]', timeout=5000)
                self.logger.info("✅ Listings loaded!")
            except Exception as e:
                self.logger.warning(f"⚠️ Timeout waiting for listings: {e}")
        
        # Extract listing URLs
        links = response.css('a::attr(href)').getall()
        seen_urls = set()
        listing_count = 0
        
        for link in links:
            if '/obiava-' in link:
                full_url = response.urljoin(link)
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    listing_count += 1
                    
                    self.logger.info(f"🚗 Found listing: {full_url[:80]}")
                    
                    # Yield request to parse listing detail
                    yield scrapy.Request(
                        full_url,
                        callback=self.parse_listing_detail,
                        dont_filter=True,
                        errback=self.errback_listing,
                        meta={
                            "playwright": True,
                            "playwright_include_page": True,
                            "playwright_page_goto_kwargs": {
                                "wait_until": "networkidle",
                                "timeout": 20000,
                            },
                        },
                    )
        
        self.listings_found += listing_count
        self.logger.info(f"✅ {brand} page {page_number}: Found {listing_count} listings (total: {self.listings_found})")
        
        # Check for next page (look for "Напред" button)
        next_page_url = None
        pagination_links = response.css('.pagination a')
        for link in pagination_links:
            link_text = link.css('::text').get()
            if link_text and 'Напред' in link_text:
                next_page_url = link.css('::attr(href)').get()
                if next_page_url:
                    next_page_url = response.urljoin(next_page_url)
                    break
        
        # Follow next page if found and under limit
        MAX_PAGES = 150
        if next_page_url and page_number < MAX_PAGES:
            next_page_number = page_number + 1
            self.logger.info(f"📄 Following {brand} to page {next_page_number}")
            
            # PRIORITY: Yield pagination request FIRST with high priority
            # This ensures we scrape all pages quickly without waiting for all listing details
            yield scrapy.Request(
                next_page_url,
                callback=self.parse_search_page,
                dont_filter=True,
                errback=self.errback_listing,
                priority=100,  # HIGH PRIORITY - process pagination before listing details
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_goto_kwargs": {
                        "wait_until": "networkidle",
                        "timeout": 20000,
                    },
                    "brand": brand,
                    "page_number": next_page_number,
                },
            )
        else:
            self.logger.info(f"✅ {brand} complete (no more pages or hit limit)")

    
    def closed(self, reason):
        """Called when spider closes - log final statistics"""
        from datetime import datetime
        end_time = datetime.now()
        duration = end_time - self.start_time if self.start_time else None
        
        self.logger.info("")
        self.logger.info("="*70)
        self.logger.info("🎉 FRESH CYCLE COMPLETE!")
        self.logger.info(f"   Brands queued: {self.total_brands}")
        self.logger.info(f"   Total listings found: {self.listings_found}")
        self.logger.info(f"   Duration: {duration}")
        self.logger.info(f"   Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"   Reason: {reason}")
        self.logger.info("="*70)
        self.logger.info("")
        self.logger.info("💡 Next cycle: Run again in 6 hours via cronjob")
