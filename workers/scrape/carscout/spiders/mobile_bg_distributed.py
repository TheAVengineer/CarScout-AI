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
        
        self.logger.info(f"👷 Distributed Worker {self.worker_id} initialized")
        self.logger.info(f"🎚️  Performance mode: {self.performance_mode}")
    
    def start_scraping(self):
        """Pull work from Redis queue and scrape - CONTINUOUS MODE"""
        
        continuous_loop_count = 0
        
        while True:
            # Get next work item
            work_item = self._get_next_work()
            
            if not work_item:
                # Queue is empty - reinitialize and continue
                continuous_loop_count += 1
                self.logger.info(f"🔄 Worker {self.worker_id}: Queue empty, reinitializing... (Cycle #{continuous_loop_count})")
                self.logger.info(f"   Completed this cycle: {self.brands_completed} brands, {self.searches_completed} searches")
                
                # Reinitialize the queue
                if self._reinitialize_queue():
                    self.logger.info(f"✅ Queue reinitialized! Starting cycle #{continuous_loop_count + 1}")
                    # Reset counters for new cycle
                    self.brands_completed = 0
                    self.searches_completed = 0
                    continue
                else:
                    self.logger.error(f"❌ Failed to reinitialize queue, stopping")
                    break
            
            self.current_brand = work_item['brand']
            self.current_searches = work_item['searches']
            model_count = work_item['model_count']
            
            self.logger.info(f"🎯 Worker {self.worker_id}: Starting brand '{self.current_brand}'")
            self.logger.info(f"   Models to scrape: {model_count}")
            
            # Scrape all models for this brand
            for search in self.current_searches:
                url = search.get('url')
                brand = search.get('brand')
                model = search.get('model', 'Unknown')
                
                if not url:
                    continue
                
                self.logger.info(f"🔍 Worker {self.worker_id}: Scraping {brand} {model}")
                
                # Yield request for this search
                yield self._create_search_request(url, search)
                
                self.searches_completed += 1
            
            # Mark brand as completed
            self._complete_work()
            self.brands_completed += 1
            
            self.logger.info(f"✅ Worker {self.worker_id}: Completed '{self.current_brand}'")
            self.logger.info(f"   Progress: {self.brands_completed} brands, {self.searches_completed} searches")
    
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
            
            # Load hybrid config
            config_path = Path(__file__).parent.parent.parent.parent.parent / "configs" / "scrape" / "mobile_bg_hybrid.json"
            
            if not config_path.exists():
                self.logger.error(f"❌ Config not found: {config_path}")
                return False
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            searches = config.get('searches', [])
            
            if not searches:
                self.logger.error(f"❌ No searches in config")
                return False
            
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
