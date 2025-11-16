"""
Mobile.bg Distributed Spider - Work Queue Based

This spider pulls work items from Redis queue:
- Each worker gets different brands
- No duplication between workers
- Workers help each other by picking up remaining work
- Progress tracked in Redis
"""

import scrapy
import redis
import json
from scrapy import signals
from scrapy.exceptions import DontCloseSpider
from .mobile_bg import MobileBgSpider


class MobileBgDistributedSpider(MobileBgSpider):
    name = "mobile_bg_distributed"
    
    def __init__(self, *args, **kwargs):
        """Initialize distributed spider with work queue"""
        super().__init__(*args, **kwargs)
        
        # Worker configuration
        self.worker_id = kwargs.get('worker_id', '1')
        self.performance_mode = kwargs.get('performance_mode', 'balanced')
        
        # Redis connection
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        
        # Work tracking
        self.current_brand = None
        self.current_searches = []
        self.brands_completed = 0
        self.searches_completed = 0
        self.current_brand_search_count = 0
        self.current_brand_search_completed = 0
        
        self.logger.info(f"👷 Distributed Worker {self.worker_id} initialized")
        self.logger.info(f"🎚️  Performance mode: {self.performance_mode}")
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(MobileBgDistributedSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider
    
    def spider_idle(self, spider):
        """Called when spider becomes idle - get next brand"""
        try:
            self.logger.info(f"⏸️  Worker {self.worker_id}: Spider idle, checking for more work...")
            
            # Mark current brand as completed if we were working on one
            if self.current_brand:
                self._complete_work()
                self.brands_completed += 1
                self.logger.info(f"✅ Worker {self.worker_id}: Completed '{self.current_brand}'")
                self.logger.info(f"   Progress: {self.brands_completed} brands, {self.searches_completed} searches")
            
            # Try to get next brand
            requests = list(self._get_next_brand_requests())
            if requests:
                # Schedule new requests
                for request in requests:
                    self.crawler.engine.crawl(request)
                # Prevent spider from closing
                raise DontCloseSpider
            else:
                self.logger.info(f"🏁 Worker {self.worker_id}: No more work available, stopping")
        
        except DontCloseSpider:
            # Re-raise DontCloseSpider to keep spider alive
            raise
        except Exception as e:
            # Log error but don't crash - let spider continue
            self.logger.error(f"❌ Error in spider_idle: {e}")
            self.logger.exception("Full traceback:")
            # Try to continue anyway by raising DontCloseSpider
            raise DontCloseSpider
    
    
    def start_requests(self):
        """Override parent's start_requests to use Redis queue"""
        self.logger.info(f"🚀 Worker {self.worker_id}: Starting distributed scraping from Redis queue")
        
        # Start by getting the first brand
        for request in self._get_next_brand_requests():
            yield request
    
    def _get_next_brand_requests(self):
        """Get requests for the next brand from Redis queue"""
        
        # Get next work item
        work_item = self._get_next_work()
        
        if not work_item:
            # Queue is empty - reinitialize and retry
            self.logger.info(f"🔄 Worker {self.worker_id}: Queue empty, reinitializing...")
            self.logger.info(f"   Completed: {self.brands_completed} brands, {self.searches_completed} searches")
            
            if self._reinitialize_queue():
                self.logger.info(f"✅ Queue reinitialized! Continuing...")
                # Reset counters for new cycle
                self.brands_completed = 0
                self.searches_completed = 0
                # Try again
                work_item = self._get_next_work()
            else:
                self.logger.error(f"❌ Failed to reinitialize queue, stopping")
                return
        
        if not work_item:
            self.logger.info(f"🏁 Worker {self.worker_id}: No more work available")
            return
        
        self.current_brand = work_item['brand']
        self.current_searches = work_item['searches']
        model_count = work_item['model_count']
        
        self.logger.info(f"🎯 Worker {self.worker_id}: Starting brand '{self.current_brand}'")
        self.logger.info(f"   Models to scrape: {model_count}")
        
        # Track how many searches for this brand
        self.current_brand_search_count = len(self.current_searches)
        self.current_brand_search_completed = 0
        
        # Scrape all models for this brand
        for search in self.current_searches:
            url = search.get('url')
            brand = search.get('brand')
            model = search.get('model', 'Unknown')
            
            if not url:
                continue
            
            self.logger.info(f"🔍 Worker {self.worker_id}: Scraping {brand} {model}")
            
            # Create request with callback that will get next brand when done
            request = self._create_search_request(url, search)
            request.meta['brand_work_item'] = work_item
            request.meta['is_last_search'] = (self.current_brand_search_completed == self.current_brand_search_count - 1)
            
            yield request
            
            self.current_brand_search_completed += 1
            self.searches_completed += 1
    
    def _get_next_work(self):
        """Get next work item from Redis queue"""
        try:
            # Atomic pop from queue
            work_json = self.redis_client.lpop("carscout:seeding:queue")
            
            if not work_json:
                return None
            
            work_item = json.loads(work_json)
            
            # Mark as processing
            processing_key = f"carscout:seeding:processing:{self.worker_id}"
            self.redis_client.set(processing_key, work_json)
            
            return work_item
        
        except Exception as e:
            self.logger.error(f"❌ Error getting work from queue: {e}")
            return None
    
    def _complete_work(self):
        """Mark current work as completed"""
        try:
            # Remove from processing
            processing_key = f"carscout:seeding:processing:{self.worker_id}"
            self.redis_client.delete(processing_key)
            
            # Add to completed set
            self.redis_client.sadd("carscout:seeding:completed", self.current_brand)
            
            # Update stats
            self.redis_client.hincrby("carscout:seeding:stats", 'completed_brands', 1)
            self.redis_client.hincrby("carscout:seeding:stats", 'completed_searches', len(self.current_searches))
            
        except Exception as e:
            self.logger.error(f"❌ Error completing work: {e}")
    
    def _create_search_request(self, url, search_config):
        """Create a request for a search page"""
        return scrapy.Request(
            url=url,
            callback=self.parse_search_page,  # Use parent spider's parse_search_page method
            errback=self.errback_listing,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_page_goto_kwargs": {
                    "wait_until": "networkidle",
                    "timeout": 30000,
                },
                "search_config": search_config,
                "max_pages": 200,
            },
        )
    
    def _reinitialize_queue(self):
        """Reinitialize the work queue when empty - enables continuous scraping"""
        try:
            import os
            import json
            from pathlib import Path
            
            # Load hybrid config from project root
            config_path = Path(__file__).parent.parent.parent.parent.parent / "mobile_bg_hybrid_config.json"
            
            if not config_path.exists():
                self.logger.error(f"❌ Config not found: {config_path}")
                return False
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Try both 'search_urls' and 'searches' keys for compatibility
            searches = config.get('search_urls', config.get('searches', []))
            
            if not searches:
                self.logger.error(f"❌ No searches in config")
                return False
            
            # USE ALL SEARCHES (both brand and model level) for maximum coverage
            self.logger.info(f"📋 Found {len(searches)} total searches in config")
            
            # Group by brand
            brands = {}
            for search in searches:
                brand = search.get('brand', 'Unknown')
                if brand not in brands:
                    brands[brand] = []
                brands[brand].append(search)
            
            # Clear old queue data
            self.redis_client.delete("carscout:seeding:queue")
            self.redis_client.delete("carscout:seeding:completed")
            
            # Push brands to queue
            for brand, brand_searches in brands.items():
                work_item = {
                    'brand': brand,
                    'searches': brand_searches,
                    'model_count': len(brand_searches)
                }
                self.redis_client.rpush("carscout:seeding:queue", json.dumps(work_item))
            
            self.logger.info(f"✅ Reinitialized queue with {len(brands)} brands, {len(searches)} searches")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error reinitializing queue: {e}")
            return False
    
    def closed(self, reason):
        """Called when spider closes"""
        self.logger.info(f"🏁 Worker {self.worker_id} finished!")
        self.logger.info(f"   Brands completed: {self.brands_completed}")
        self.logger.info(f"   Searches completed: {self.searches_completed}")
        self.logger.info(f"   Reason: {reason}")
        
        # Clean up processing marker
        try:
            processing_key = f"carscout:seeding:processing:{self.worker_id}"
            self.redis_client.delete(processing_key)
        except:
            pass
