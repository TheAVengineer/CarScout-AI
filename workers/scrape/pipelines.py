"""
Scrapy pipeline to save scraped listings to database
"""
from datetime import datetime
from uuid import UUID

from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw, Source
from workers.pipeline.tasks.parse import parse_listing


class CarScoutPipeline:
    """Pipeline to process scraped items"""
    
    def open_spider(self, spider):
        """Initialize when spider opens"""
        self.session = get_sync_session()
        spider.logger.info("CarScoutPipeline initialized")
    
    def close_spider(self, spider):
        """Cleanup when spider closes"""
        if hasattr(self, 'session'):
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
                    first_seen_at=datetime.utcnow(),
                    last_seen_at=datetime.utcnow(),
                    is_active=item.get('is_active', True),
                )
                self.session.add(listing_raw)
                spider.logger.info(f"Created new listing {item['site_ad_id']}")
            
            self.session.commit()
            
            # Trigger async parsing task
            # In production, upload raw_html to S3 first
            parse_listing.delay(
                listing_id=str(listing_raw.id),
                raw_html_path=item.get('raw_html_path', ''),
                source_id=item['source_id'],
            )
            
            return item
            
        except Exception as e:
            spider.logger.error(f"Error processing item: {e}")
            self.session.rollback()
            raise
