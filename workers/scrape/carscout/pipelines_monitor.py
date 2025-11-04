"""
Deal Monitor Pipeline

Purpose: Process new listings from monitor spider
Flow:
1. Check if listing is new (not in database)
2. Apply pre-filters (price, mileage, year, transmission)
3. If passes filters → Evaluate with AI
4. If score ≥ 7.5 → Post to Telegram channel
5. Store in database

This pipeline is optimized for real-time deal detection.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
import sys
import os
from pathlib import Path

# Add project root to path (go up from pipelines_monitor.py -> carscout -> scrape -> workers -> project root)
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
os.chdir(str(project_root))  # Change to project root for imports

from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw, Source
# from libs.domain.scoring import calculate_listing_score  # TODO: implement this
# from libs.ml.risk_evaluation import evaluate_listing_risk  # TODO: implement this
# from libs.ml.pricing import predict_price_range  # TODO: implement this
from configs.settings import settings

logger = logging.getLogger(__name__)


class DealMonitorPipeline:
    """Pipeline for monitoring and posting new deals"""
    
    def __init__(self):
        self.session: Optional[Session] = None
        self.stats = {
            'total_scraped': 0,
            'new_listings': 0,
            'duplicates': 0,
            'filtered_out': 0,
            'evaluated': 0,
            'posted_to_channel': 0,
        }
        
        # Pre-load existing listing IDs for fast duplicate check
        self.existing_ids = set()
        
        logger.info("🔍 DealMonitorPipeline initialized")
    
    def open_spider(self, spider):
        """Initialize database session and load existing IDs"""
        self.session = get_sync_session()
        
        # Get the source (mobile_bg) from database
        source = self.session.query(Source).filter_by(name='mobile_bg').first()
        if not source:
            # Create source if it doesn't exist
            source = Source(
                name='mobile_bg',
                base_url='https://www.mobile.bg',
                source_type='marketplace'
            )
            self.session.add(source)
            self.session.commit()
        self.source_id = source.id
        
        # Load all existing listing IDs into memory for fast lookup
        logger.info("📥 Loading existing listing IDs...")
        result = self.session.execute(
            select(ListingRaw.site_ad_id).where(
                ListingRaw.source_id == self.source_id
            )
        )
        self.existing_ids = {row[0] for row in result}
        logger.info(f"✅ Loaded {len(self.existing_ids)} existing listing IDs")
    
    def close_spider(self, spider):
        """Close database session and log statistics"""
        if self.session:
            self.session.close()
        
        logger.info("=" * 60)
        logger.info("📊 MONITOR RUN STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total Scraped:       {self.stats['total_scraped']}")
        logger.info(f"New Listings:        {self.stats['new_listings']}")
        logger.info(f"Duplicates:          {self.stats['duplicates']}")
        logger.info(f"Filtered Out:        {self.stats['filtered_out']}")
        logger.info(f"AI Evaluated:        {self.stats['evaluated']}")
        logger.info(f"Posted to Channel:   {self.stats['posted_to_channel']}")
        logger.info("=" * 60)
    
    def process_item(self, item, spider):
        """Process each scraped listing"""
        self.stats['total_scraped'] += 1
        
        site_ad_id = item.get('site_ad_id')
        if not site_ad_id:
            logger.warning("⚠️ Item missing site_ad_id, skipping")
            return item
        
        # 1. CHECK IF NEW LISTING
        if site_ad_id in self.existing_ids:
            self.stats['duplicates'] += 1
            logger.debug(f"⏭️ Duplicate: {site_ad_id}")
            return item  # Skip duplicates
        
        self.stats['new_listings'] += 1
        logger.info(f"🆕 NEW LISTING: {site_ad_id}")
        
        # 2. APPLY PRE-FILTERS
        target_config = item.get('target_config', {})
        filters = target_config.get('filters', {})
        
        if not self._passes_filters(item, filters):
            self.stats['filtered_out'] += 1
            logger.info(f"🚫 Filtered out: {site_ad_id} (doesn't meet criteria)")
            # Still save to database, but don't evaluate with AI
            self._save_to_database(item, evaluated=False, posted=False)
            return item
        
        logger.info(f"✅ Passed filters: {site_ad_id}")
        
        # 3. AI EVALUATION (only for promising listings)
        score, evaluation_data = self._evaluate_with_ai(item)
        
        self.stats['evaluated'] += 1
        logger.info(f"🤖 AI Score: {score:.2f}/10 for {site_ad_id}")
        
        # 4. POST TO TELEGRAM IF GOOD DEAL
        min_score = target_config.get('ai_evaluation', {}).get('min_score_to_post', 7.5)
        
        if score >= min_score:
            posted = self._post_to_telegram(item, score, evaluation_data)
            if posted:
                self.stats['posted_to_channel'] += 1
                logger.info(f"📢 Posted to Telegram: {site_ad_id} (score {score:.2f})")
        else:
            posted = False
            logger.info(f"📉 Score too low to post: {score:.2f} < {min_score}")
        
        # 5. SAVE TO DATABASE
        self._save_to_database(item, evaluated=True, posted=posted, score=score)
        
        # Add to existing IDs to prevent re-processing in same run
        self.existing_ids.add(site_ad_id)
        
        return item
    
    def _passes_filters(self, item: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if listing passes pre-filters"""
        
        # Price filter
        if 'price_max' in filters:
            price = item.get('price')
            if price is None or price > filters['price_max']:
                logger.debug(f"❌ Price filter failed: {price} > {filters['price_max']}")
                return False
        
        if 'price_min' in filters:
            price = item.get('price')
            if price is None or price < filters['price_min']:
                logger.debug(f"❌ Price filter failed: {price} < {filters['price_min']}")
                return False
        
        # Year filter
        if 'year_min' in filters:
            year = item.get('year')
            if year is None or year < filters['year_min']:
                logger.debug(f"❌ Year filter failed: {year} < {filters['year_min']}")
                return False
        
        if 'year_max' in filters:
            year = item.get('year')
            if year is None or year > filters['year_max']:
                logger.debug(f"❌ Year filter failed: {year} > {filters['year_max']}")
                return False
        
        # Mileage filter
        if 'mileage_max' in filters:
            mileage = item.get('mileage')
            if mileage is None or mileage > filters['mileage_max']:
                logger.debug(f"❌ Mileage filter failed: {mileage} > {filters['mileage_max']}")
                return False
        
        # Transmission filter
        if 'transmission' in filters:
            allowed_transmissions = filters['transmission']
            if isinstance(allowed_transmissions, str):
                allowed_transmissions = [allowed_transmissions]
            
            transmission = item.get('transmission', '').lower()
            if not any(t.lower() in transmission for t in allowed_transmissions):
                logger.debug(f"❌ Transmission filter failed: {transmission} not in {allowed_transmissions}")
                return False
        
        # Fuel type filter
        if 'fuel_type' in filters:
            allowed_fuels = filters['fuel_type']
            if isinstance(allowed_fuels, str):
                allowed_fuels = [allowed_fuels]
            
            fuel = item.get('fuel_type', '').lower()
            if not any(f.lower() in fuel for f in allowed_fuels):
                logger.debug(f"❌ Fuel type filter failed: {fuel} not in {allowed_fuels}")
                return False
        
        # Power filter (PS)
        if 'power_min' in filters:
            power = item.get('power_ps')
            if power is None or power < filters['power_min']:
                logger.debug(f"❌ Power filter failed: {power} < {filters['power_min']}")
                return False
        
        logger.debug("✅ All filters passed")
        return True
    
    def _evaluate_with_ai(self, item: Dict[str, Any]) -> tuple[float, Dict[str, Any]]:
        """Evaluate listing with AI (risk + pricing + scoring)
        
        TODO: Implement real ML models for:
        - Risk evaluation (fraud detection)
        - Price prediction
        - Deal scoring
        
        For now, using simple heuristics.
        """
        
        evaluation_data = {}
        
        try:
            # Simple heuristic scoring until ML models are implemented
            score = 7.0  # Default score
            
            # Bonus points for good attributes
            if item.get('year', 0) >= 2020:
                score += 0.5  # Newer cars
            
            if item.get('mileage', 999999) < 50000:
                score += 0.5  # Low mileage
            
            price = item.get('price', 0)
            if 20000 <= price <= 80000:
                score += 0.5  # Mid-range pricing (sweet spot)
            
            if item.get('transmission', '').lower() in ['автоматична', 'automatic']:
                score += 0.3  # Automatic transmission preferred
            
            if item.get('fuel_type', '').lower() in ['хибрид', 'електричество', 'hybrid', 'electric']:
                score += 0.7  # Eco-friendly bonus
            
            # Cap at 10
            score = min(10.0, score)
            
            evaluation_data['risk'] = {'level': 'low', 'score': 0.2}
            evaluation_data['pricing'] = {
                'p50': price * 1.1 if price else 0,  # Assume 10% discount
                'deal_quality': 10.0  # Percentage discount
            }
            evaluation_data['note'] = 'Using heuristic scoring - ML models not yet implemented'
            
            return score, evaluation_data
        
        except Exception as e:
            logger.error(f"Error during AI evaluation: {e}")
            # Return neutral score on error
            return 5.0, {'error': str(e)}
    
    def _post_to_telegram(self, item: Dict[str, Any], score: float, evaluation_data: Dict[str, Any]) -> bool:
        """Post listing to Telegram channel"""
        
        try:
            from workers.pipeline.tasks.notify import post_to_channel
            
            # Format message
            brand = item.get('brand', 'Unknown')
            model = item.get('model', 'Unknown')
            year = item.get('year', 'N/A')
            price = item.get('price', 'N/A')
            currency = item.get('currency', 'BGN')
            mileage = item.get('mileage', 'N/A')
            
            # Get price analysis
            pricing = evaluation_data.get('pricing', {})
            predicted_price = pricing.get('p50', price)
            deal_quality = ((predicted_price - price) / predicted_price * 100) if predicted_price and price else 0
            
            message = f"""
🚨 **NEW DEAL ALERT** 🚨

🏆 Score: **{score:.1f}/10**

🚗 **{brand} {model}**
📅 Year: {year}
💰 Price: **{price:,} {currency}**
📏 Mileage: {mileage:,} km

📊 **Analysis:**
- Predicted value: {predicted_price:,} {currency}
- Deal quality: **{deal_quality:+.1f}%**
- Risk level: {evaluation_data.get('risk', {}).get('level', 'Unknown')}

🔗 [View Listing]({item.get('url')})

⏰ Posted: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
            
            # Post to channel
            post_to_channel(
                message=message,
                images=item.get('images', [])[:3],  # First 3 images
                listing_url=item.get('url')
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error posting to Telegram: {e}")
            return False
    
    def _save_to_database(self, item: Dict[str, Any], evaluated: bool = False, posted: bool = False, score: Optional[float] = None):
        """Save listing to database"""
        
        try:
            listing = ListingRaw(
                source_id=self.source_id,
                site_ad_id=item.get('site_ad_id'),
                url=item.get('url'),
                raw_html_path=None,  # Monitor doesn't save HTML
                parsed_data={
                    'brand': item.get('brand'),
                    'model': item.get('model'),
                    'year': item.get('year'),
                    'price': item.get('price'),
                    'currency': item.get('currency'),
                    'mileage': item.get('mileage'),
                    'power_ps': item.get('power_ps'),
                    'fuel_type': item.get('fuel_type'),
                    'transmission': item.get('transmission'),
                    'body_type': item.get('body_type'),
                    'description': item.get('description'),
                    'location': item.get('location'),
                    'images': item.get('images'),
                    'seller_phone': item.get('seller_phone'),
                    'scraped_at': item.get('scraped_at'),
                    'monitor_metadata': {
                        'evaluated': evaluated,
                        'posted_to_channel': posted,
                        'score': score,
                        'discovered_by': 'monitor',
                    }
                },
                first_seen_at=datetime.now(),
                last_seen_at=datetime.now(),
                is_active=True,
            )
            
            self.session.add(listing)
            self.session.commit()
            
            logger.debug(f"💾 Saved to database: {item.get('site_ad_id')}")
        
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            self.session.rollback()
