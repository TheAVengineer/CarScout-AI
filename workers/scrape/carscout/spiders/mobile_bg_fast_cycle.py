"""
Mobile.bg FAST Fresh Cycle Spider - URL Collector Only

This spider is designed for SPEED:
- Scrapes search pages ONLY (no listing details)
- Collects URLs from last 2 days (sort=7)
- No login required (public search pages)
- Completes in ~5-10 minutes (vs hours for full scrape)
- URLs are stored in database for later detail parsing

Architecture:
1. Fast search page scraping (all brands, all pages)
2. Extract listing URLs only
3. Store URLs in database with timestamp
4. Separate worker parses listing details later
"""

import scrapy
from datetime import datetime
from typing import Iterator


class MobileBgFastCycleSpider(scrapy.Spider):
    """Ultra-fast URL collector for fresh Mobile.bg listings"""
    
    name = "mobile_bg_fast_cycle"
    allowed_domains = ['mobile.bg']
    
    BRANDS = [
        'mercedes-benz', 'bmw', 'audi', 'volkswagen', 'opel',
        'ford', 'toyota', 'renault', 'peugeot', 'citroen',
        'skoda', 'seat', 'honda', 'mazda', 'nissan',
        'hyundai', 'kia', 'volvo', 'fiat', 'alfa-romeo',
    ]
    
    custom_settings = {
        # FAST settings - no Playwright for listing details
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 0.3,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 0.3,
        'AUTOTHROTTLE_MAX_DELAY': 2,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 10.0,
        
        # Simple pipeline that just stores URLs
        'ITEM_PIPELINES': {
            'carscout.pipeline_fast_url.FastURLPipeline': 100,
        },
        
        'CLOSESPIDER_TIMEOUT': 900,  # Max 15 minutes
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = None
        self.urls_collected = 0
        self.pages_scraped = 0
    
    def start_requests(self) -> Iterator[scrapy.Request]:
        """Start scraping - NO LOGIN REQUIRED for public search pages"""
        self.start_time = datetime.now()
        
        self.logger.info("="*80)
        self.logger.info("⚡ FAST FRESH CYCLE - URL COLLECTION MODE")
        self.logger.info(f"   📋 Brands: {len(self.BRANDS)}")
        self.logger.info(f"   🎯 Filter: Last 2 days (sort=7)")
        self.logger.info(f"   🚀 Mode: URLs only (FAST - no listing details)")
        self.logger.info(f"   🔓 Auth: None required (public search pages)")
        self.logger.info(f"   ⏰ Started: {self.start_time.strftime('%H:%M:%S')}")
        self.logger.info("="*80)
        
        for brand in self.BRANDS:
            url = f"https://www.mobile.bg/obiavi/avtomobili-dzhipove/{brand}/namira-se-v-balgariya?sort=7"
            
            yield scrapy.Request(
                url,
                callback=self.parse_search_page,
                meta={
                    'brand': brand,
                    'page_number': 1,
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_goto_kwargs': {
                        'wait_until': 'domcontentloaded',  # Faster!
                        'timeout': 10000,
                    },
                },
                dont_filter=True,
                priority=100,
            )
    
    async def parse_search_page(self, response):
        """Extract URLs from search page - FAST (no detail parsing)"""
        brand = response.meta.get('brand', 'unknown')
        page_number = response.meta.get('page_number', 1)
        
        # Wait for listings to load
        playwright_page = response.meta.get("playwright_page")
        if playwright_page:
            try:
                await playwright_page.wait_for_selector('a[href*="/obiava-"]', timeout=5000)
            except Exception as e:
                self.logger.warning(f"⚠️ Timeout waiting for listings: {e}")
        
        # Extract ALL listing URLs (fast CSS selector)
        listing_links = response.css('a[href*="/obiava-"]::attr(href)').getall()
        unique_urls = list(set(listing_links))  # Dedupe
        
        # Yield items with minimal data (just URL + timestamp)
        for url in unique_urls:
            full_url = response.urljoin(url)
            
            # Extract site_ad_id from URL
            site_ad_id = full_url.split('/obiava-')[1].split('-')[0] if '/obiava-' in full_url else None
            
            if site_ad_id:
                self.urls_collected += 1
                
                # Yield minimal item (pipeline will handle storage)
                yield {
                    'site_ad_id': site_ad_id,
                    'url': full_url,
                    'brand_hint': brand,
                    'discovered_at': datetime.now().isoformat(),
                    'source': 'mobile_bg',
                    'sort_filter': 'last_2_days',
                    # Note: No listing details! These will be parsed later by separate worker
                }
        
        self.pages_scraped += 1
        self.logger.info(f"✅ {brand} p{page_number}: {len(unique_urls)} URLs (total: {self.urls_collected})")
        
        # Check for next page
        next_page_url = None
        pagination_links = response.css('.pagination a')
        
        for link in pagination_links:
            link_text = link.css('::text').get()
            if link_text and 'Напред' in link_text:
                next_page_url = link.css('::attr(href)').get()
                if next_page_url:
                    next_page_url = response.urljoin(next_page_url)
                    break
        
        # Follow to next page (HIGH PRIORITY - process before listing details)
        MAX_PAGES = 150
        if next_page_url and page_number < MAX_PAGES:
            self.logger.info(f"➡️  {brand} → page {page_number + 1}")
            
            yield scrapy.Request(
                next_page_url,
                callback=self.parse_search_page,
                meta={
                    'brand': brand,
                    'page_number': page_number + 1,
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_goto_kwargs': {
                        'wait_until': 'domcontentloaded',
                        'timeout': 10000,
                    },
                },
                dont_filter=True,
                priority=100,  # Keep search pages at high priority
            )
        else:
            self.logger.info(f"✅ {brand} complete!")
    
    def closed(self, reason):
        """Spider finished - log summary"""
        if self.start_time:
            duration = datetime.now() - self.start_time
            
            self.logger.info("="*80)
            self.logger.info("⚡ FAST CYCLE COMPLETE")
            self.logger.info(f"   📄 Pages scraped: {self.pages_scraped}")
            self.logger.info(f"   🔗 URLs collected: {self.urls_collected}")
            self.logger.info(f"   ⏱️  Duration: {duration}")
            self.logger.info(f"   📊 Speed: {self.urls_collected / duration.total_seconds():.1f} URLs/sec")
            self.logger.info("="*80)
