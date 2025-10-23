"""
Scrapy pipeline to save scraped listings to database
"""
import sys
from datetime import datetime
from pathlib import Path
from uuid import UUID

# Add project root to path to find configs, libs, workers modules
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw, Source
from workers.pipeline.tasks.parse import parse_listing


class CarScoutPipeline:
    """Pipeline to process scraped items"""
    
    def open_spider(self, spider):
        """Initialize when spider opens"""
        self.session = get_sync_session()
        self.seen_listings = set()  # Track listings seen in this scrape run
        self.scrape_start_time = datetime.utcnow()
        spider.logger.info(f"CarScoutPipeline initialized at {self.scrape_start_time}")
    
    def close_spider(self, spider):
        """Cleanup when spider closes"""
        if hasattr(self, 'session'):
            # Mark listings not seen in this scrape as inactive
            try:
                source = self.session.query(Source).filter_by(name='mobile_bg').first()
                if source and hasattr(self, 'seen_listings'):
                    # Get all previously active listings from this source
                    all_active = self.session.query(ListingRaw).filter_by(
                        source_id=source.id,
                        is_active=True
                    ).all()
                    
                    # Mark as inactive if not seen in this scrape
                    inactive_count = 0
                    for listing in all_active:
                        if listing.site_ad_id not in self.seen_listings:
                            listing.is_active = False
                            inactive_count += 1
                    
                    if inactive_count > 0:
                        self.session.commit()
                        spider.logger.info(f"✅ Marked {inactive_count} listings as inactive (no longer on website)")
                    
                    spider.logger.info(f"📊 Scrape Summary:")
                    spider.logger.info(f"   - Total listings seen: {len(self.seen_listings)}")
                    spider.logger.info(f"   - Marked inactive: {inactive_count}")
                    
            except Exception as e:
                spider.logger.error(f"Error marking inactive listings: {e}")
                self.session.rollback()
            finally:
                self.session.close()
                
        spider.logger.info("CarScoutPipeline closed")
    
    def process_item(self, item, spider):
        """Process each scraped item"""
        try:
            # Get or create source
            source = self.session.query(Source).filter_by(name=item['source_id']).first()
            if not source:
                source = Source(
                    name=item['source_id'],
                    base_url=f"https://www.{item['source_id']}.bg",
                    enabled=True,
                )
                self.session.add(source)
                self.session.flush()
            
            # Check if listing already exists
            existing = self.session.query(ListingRaw).filter_by(
                source_id=source.id,
                site_ad_id=item['site_ad_id']
            ).first()
            
            # Track this listing as seen in current scrape
            self.seen_listings.add(item['site_ad_id'])
            
            if existing:
                # Update existing listing
                existing.last_seen_at = datetime.utcnow()
                existing.is_active = item.get('is_active', True)
                existing.url = item['url']
                listing_raw = existing
                spider.logger.info(f"Updated existing listing {item['site_ad_id']}")
            else:
                # Create new listing
                listing_raw = ListingRaw(
                    id=UUID(item['listing_id']),
                    source_id=source.id,
                    site_ad_id=item['site_ad_id'],
                    url=item['url'],
                    raw_html_path=item.get('raw_html_path'),
                    raw_html=None,  # Don't store HTML in DB (save to S3 in production)
                    parsed_data={  # Store spider-extracted data
                        'brand': item.get('brand'),
                        'model': item.get('model'),
                        'year': item.get('year'),
                        'mileage_km': item.get('mileage_km'),
                        'fuel': item.get('fuel'),
                        'gearbox': item.get('gearbox'),
                        'price': item.get('price'),
                        'currency': item.get('currency'),
                        'region': item.get('region'),
                        'title': item.get('title'),
                        'description': item.get('description'),
                        'images': item.get('images', []),
                        'phone_hash': item.get('phone_hash'),
                    },
                    first_seen_at=datetime.utcnow(),
                    last_seen_at=datetime.utcnow(),
                    is_active=item.get('is_active', True),
                )
                self.session.add(listing_raw)
                spider.logger.info(f"Created new listing {item['site_ad_id']}")
            
            self.session.commit()
            
            # Trigger async parsing task
            # In production, upload raw_html to S3 first
            parse_listing.delay(str(listing_raw.id))
            
            return item
            
        except Exception as e:
            spider.logger.error(f"Error processing item: {e}")
            self.session.rollback()
            raise
