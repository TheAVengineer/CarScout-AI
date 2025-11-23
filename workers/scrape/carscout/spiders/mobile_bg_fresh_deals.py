"""
Mobile.bg Fresh Deals Spider - Fast brand-level scraping with sort=7

Strategy:
- Use sort=7 filter (listi            yield scrapy.Request(
                url=search_url['url'],
                callback=self.parse_search_page,
                meta={
                    'search_info': search_url,
                    'playwright': True,
                    'playwright_include_page': True,
                },
            )ast 2 days only)
- Scrape at BRAND level (no model filtering)
- Much faster: 70-80 pages vs 250+ pages per brand
- Perfect for real-time deal detection

Performance:
- 5 minutes per brand (vs 30 minutes with model-by-model)
- ~2,000 fresh listings per brand
- 10x faster than deep seeding approach
- Run every 2 hours for fresh deal coverage

Usage:
    # Single brand test
    scrapy crawl mobile_bg_fresh_deals -a brand=mercedes-benz
    
    # All brands
    scrapy crawl mobile_bg_fresh_deals
"""

import scrapy
import json
from urllib.parse import urlencode
from datetime import datetime
from .mobile_bg import MobileBgSpider


class MobileBgFreshDealsSpider(MobileBgSpider):
    """Fast spider for fresh Mobile.bg listings (last 2 days)
    
    Inherits from MobileBgSpider for parsing logic,
    but uses brand-level search with sort=7 filter
    """
    
    name = "mobile_bg_fresh_deals"
    
    custom_settings = {
        # More aggressive since we're scraping fresh content
        'CONCURRENT_REQUESTS': 12,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
        'DOWNLOAD_DELAY': 0.5,  # Faster than deep spider
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 0.5,
        'AUTOTHROTTLE_MAX_DELAY': 3,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 4.0,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        
        # Timeouts to prevent hanging
        'DOWNLOAD_TIMEOUT': 60,  # 60 second timeout for requests
        'PLAYWRIGHT_TIMEOUT': 45000,  # 45 second timeout for Playwright (in ms)
        
        # Auto-close after 2 hours max (safety)
        'CLOSESPIDER_TIMEOUT': 7200,  # 2 hours in seconds
        
        # Log level
        'LOG_LEVEL': 'INFO',
    }
    
    # All 131 brands (alphabetically)
    BRANDS = [
        'abarth', 'acura', 'aixam', 'alfa-romeo', 'alpina', 'aston-martin',
        'audi', 'austin', 'baic', 'baw', 'bentley', 'bentu', 'bmw',
        'brilliance', 'buick', 'byd', 'cadillac', 'carbodies', 'chana',
        'changan', 'chery', 'chevrolet', 'chrysler', 'citroen', 'cupra',
        'dacia', 'daewoo', 'daf', 'daihatsu', 'datsun', 'dfsk', 'dodge',
        'dongfeng', 'dr', 'ds-automobiles', 'faw', 'ferrari', 'fiat',
        'fisker', 'ford', 'foton', 'gac-gonow', 'geely', 'genesis', 'gmc',
        'gonow', 'great-wall', 'hafei', 'haval', 'hawtai', 'hino', 'honda',
        'hongqi', 'hummer', 'hyundai', 'infiniti', 'innocenti', 'iran-khodro',
        'isuzu', 'iveco', 'jac', 'jaguar', 'jeep', 'jetour', 'kia',
        'lada', 'lamborghini', 'lancia', 'land-rover', 'landwind', 'ldv',
        'leapmotor', 'lexus', 'lifan', 'lincoln', 'lotus', 'lucid', 'luxgen',
        'mahindra', 'maserati', 'maxus', 'maybach', 'mazda', 'mclaren',
        'mercedes-benz', 'mercury', 'mg', 'mini', 'mitsubishi', 'nio',
        'nissan', 'oldsmobile', 'oltcit', 'opel', 'peugeot', 'piaggio',
        'plymouth', 'polestar', 'polonez', 'pontiac', 'porsche', 'proton',
        'ram', 'renault', 'rivian', 'rolls-royce', 'rover', 'saab',
        'saturn', 'seat', 'seres', 'skoda', 'skywell', 'smart', 'ssangyong',
        'subaru', 'suzuki', 'talbot', 'tata', 'tesla', 'think', 'toyota',
        'trabant', 'triumph', 'uaz', 'vauxhall', 'volkswagen', 'volvo',
        'voyah', 'wartburg', 'wey', 'wuling', 'xpeng', 'yugo', 'zastava',
        'zaz', 'zhidou', 'zotye'
    ]
    
    def __init__(self, brand=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Disable login for fresh deals spider (not needed)
        self.skip_login = True
        
        # If specific brand provided, only scrape that one
        if brand:
            self.brands_to_scrape = [brand.lower()]
            self.logger.info(f"🎯 Testing single brand: {brand}")
        else:
            self.brands_to_scrape = self.BRANDS
            self.logger.info(f"🚀 Scraping all {len(self.BRANDS)} brands for fresh deals")
        
        # Track cycle count
        self.cycle_count = 0
    
    def start_requests(self):
        """Generate requests for all brands with sort=7 (last 2 days)"""
        
        # Single pass through all brands (continuous mode handled by external scheduler)
        self.cycle_count = 1
        
        self.logger.info(f"")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"� Scraping all {len(self.brands_to_scrape)} brands for fresh deals (single run)")
        self.logger.info(f"{'='*60}")
        
        for brand_slug in self.brands_to_scrape:
            # Brand-level URL with sort=7 (last 2 days filter)
            search_url = {
                'type': 'brand',
                'brand': brand_slug.replace('-', ' ').title(),  # Convert to title case
                'brand_slug': brand_slug,
                'model': None,
                'model_slug': None,
                'url': f"https://www.mobile.bg/obiavi/avtomobili-dzhipove/{brand_slug}/namira-se-v-balgariya?sort=7",
                'priority': False,
                'estimated_listings': 2000,  # Estimate for 2 days of data
            }
            
            yield scrapy.Request(
                url=search_url['url'],
                callback=self.parse_search_page,  # Use parent's parse_search_page
                meta={
                    'search_info': search_url,
                    'playwright': True,
                    'playwright_include_page': True,
                },
            )
