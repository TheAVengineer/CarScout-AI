"""
Fast URL Collection Pipeline

Stores listing URLs discovered during fast cycles without parsing details.
URLs are stored with discovery timestamp for later detail scraping.
"""

from datetime import datetime
from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw, Source


class FastURLPipeline:
    """Minimal pipeline that just stores URLs for later processing"""
    
    def __init__(self):
        self.session = None
        self.source_id = None
        self.urls_stored = 0
        self.urls_updated = 0 
    
    def open_spider(self, spider):
        """Initialize database session"""
        self.session = get_sync_session()
        
        # Get or create source
        source = self.session.query(Source).filter_by(name='mobile_bg').first()
        if not source:
            source = Source(
                name='mobile_bg',
                base_url='https://www.mobile.bg',
                enabled=True,
            )
            self.session.add(source)
            self.session.commit()
        
        self.source_id = source.id
        spider.logger.info("✅ FastURLPipeline initialized")
    
    def close_spider(self, spider):
        """Commit and close"""
        if self.session:
            self.session.commit()
            self.session.close()
        
        spider.logger.info(f"✅ FastURLPipeline: {self.urls_stored} stored, {self.urls_updated} updated")
    
    def process_item(self, item, spider):
        """Store URL with minimal data"""
        try:
            site_ad_id = item['site_ad_id']
            url = item['url']
            
            # Check if listing exists
            existing = self.session.query(ListingRaw).filter_by(
                source_id=self.source_id,
                site_ad_id=site_ad_id
            ).first()
            
            if existing:
                # Update last_seen_at
                existing.last_seen_at = datetime.utcnow()
                existing.is_active = True
                existing.url = url
                self.urls_updated += 1
            else:
                # Create new minimal listing record
                listing = ListingRaw(
                    source_id=self.source_id,
                    site_ad_id=site_ad_id,
                    url=url,
                    raw_html_path=None,
                    raw_html=None,
                    parsed_data={'brand_hint': item.get('brand_hint')},
                    is_active=True,
                    last_seen_at=datetime.utcnow(),
                )
                self.session.add(listing)
                self.urls_stored += 1
            
            # Commit every 100 items
            if (self.urls_stored + self.urls_updated) % 100 == 0:
                self.session.commit()
                spider.logger.info(f"💾 Saved batch: {self.urls_stored} new, {self.urls_updated} updated")
            
            return item
            
        except Exception as e:
            spider.logger.error(f"❌ Error storing URL {item.get('site_ad_id')}: {e}")
            self.session.rollback()
            return item
