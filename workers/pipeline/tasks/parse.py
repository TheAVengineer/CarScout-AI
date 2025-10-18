"""
Parse task - extract structured data from raw HTML
"""
import re
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
from bs4 import BeautifulSoup

from workers.pipeline.celery_app import celery_app
from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw, ListingNormalized
from workers.pipeline.tasks.normalize import normalize_listing

logger = logging.getLogger(__name__)


class MobileBgParser:
    """Parser for Mobile.bg HTML"""
    
    @staticmethod
    def parse(html: str, url: str) -> Optional[Dict[str, Any]]:
        """Parse Mobile.bg listing page"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title_elem = soup.select_one('h1.titleItem, h1.adPage__header__title')
            title = title_elem.text.strip() if title_elem else None
            
            # Extract price
            price_elem = soup.select_one('.price, .adPage__price')
            price_text = price_elem.text.strip() if price_elem else None
            price = None
            currency = 'BGN'
            
            if price_text:
                # Extract number and currency
                price_match = re.search(r'([\d\s]+)\s*(лв|EUR|€)', price_text)
                if price_match:
                    price = int(price_match.group(1).replace(' ', ''))
                    currency_text = price_match.group(2)
                    if currency_text in ['EUR', '€']:
                        currency = 'EUR'
            
            # Extract details table
            details = {}
            detail_rows = soup.select('.dilarData tr, .adPage__content__features tr')
            for row in detail_rows:
                cells = row.find_all('td')
                if len(cells) == 2:
                    key = cells[0].text.strip().rstrip(':')
                    value = cells[1].text.strip()
                    details[key] = value
            
            # Extract brand and model from title or details
            brand = details.get('Марка', None)
            model = details.get('Модел', None)
            
            # Try to extract from title if not in details
            if not brand and title:
                # Common pattern: "BMW 520 D - touring"
                parts = title.split()
                if len(parts) > 0:
                    brand = parts[0]
                if len(parts) > 1:
                    model = ' '.join(parts[1:3])  # Take next 1-2 words
            
            # Extract other fields
            year_text = details.get('Година', details.get('Първа регистрация', ''))
            year = None
            if year_text:
                year_match = re.search(r'(\d{4})', year_text)
                if year_match:
                    year = int(year_match.group(1))
            
            mileage_text = details.get('Пробег', '')
            mileage = None
            if mileage_text:
                mileage_match = re.search(r'([\d\s]+)', mileage_text.replace('км', ''))
                if mileage_match:
                    mileage = int(mileage_match.group(1).replace(' ', ''))
            
            fuel_type = details.get('Гориво', None)
            gearbox = details.get('Скоростна кутия', None)
            body_type = details.get('Категория', None)
            color = details.get('Цвят', None)
            region = details.get('Населено място', None)
            
            # Extract engine info
            engine_text = details.get('Двигател', '')
            engine_power = None
            engine_volume = None
            
            if engine_text:
                # Extract HP
                hp_match = re.search(r'(\d+)\s*к\.с', engine_text)
                if hp_match:
                    engine_power = int(hp_match.group(1))
                
                # Extract volume
                vol_match = re.search(r'(\d+)\s*куб', engine_text)
                if vol_match:
                    engine_volume = int(vol_match.group(1))
            
            # Extract description
            desc_elem = soup.select_one('.description, .adPage__content__description')
            description = desc_elem.text.strip() if desc_elem else None
            
            # Extract images
            images = []
            img_elements = soup.select('.pic img, .adPage__gallery img, .thumbs img')
            for img in img_elements:
                src = img.get('src', img.get('data-src', ''))
                if src and 'no-image' not in src:
                    # Convert thumbnail to full size
                    full_src = src.replace('_Small', '').replace('_Thumb', '')
                    if full_src.startswith('//'):
                        full_src = 'https:' + full_src
                    elif full_src.startswith('/'):
                        full_src = 'https://www.mobile.bg' + full_src
                    images.append(full_src)
            
            # Remove duplicates while preserving order
            images = list(dict.fromkeys(images))
            
            # Extract phone (if visible)
            phone_elem = soup.select_one('.phone, .adPage__phone')
            phone = phone_elem.text.strip() if phone_elem else None
            
            # Extract seller name
            seller_elem = soup.select_one('.sellerName, .adPage__seller__name')
            seller_name = seller_elem.text.strip() if seller_elem else None
            
            return {
                'title': title,
                'brand': brand,
                'model': model,
                'year': year,
                'mileage_km': mileage,
                'price': price,
                'currency': currency,
                'fuel_type': fuel_type,
                'gearbox': gearbox,
                'body_type': body_type,
                'color': color,
                'engine_power_hp': engine_power,
                'engine_volume_cc': engine_volume,
                'region': region,
                'description': description,
                'images': images[:5],  # Limit to 5 images
                'phone': phone,
                'seller_name': seller_name,
                'raw_details': details,
            }
            
        except Exception as e:
            logger.error(f"Failed to parse Mobile.bg HTML: {e}", exc_info=True)
            return None


class CarsBgParser:
    """Parser for Cars.bg HTML"""
    
    @staticmethod
    def parse(html: str, url: str) -> Optional[Dict[str, Any]]:
        """Parse Cars.bg listing page"""
        # TODO: Implement Cars.bg parser
        logger.warning("Cars.bg parser not implemented yet")
        return None


class OlxParser:
    """Parser for OLX HTML"""
    
    @staticmethod
    def parse(html: str, url: str) -> Optional[Dict[str, Any]]:
        """Parse OLX listing page"""
        # TODO: Implement OLX parser
        logger.warning("OLX parser not implemented yet")
        return None


PARSERS = {
    'mobile_bg': MobileBgParser,
    'cars_bg': CarsBgParser,
    'olx_bg': OlxParser,
}


@celery_app.task(bind=True, max_retries=3)
def parse_listing(self, listing_raw_id: str):
    """Parse raw listing HTML to structured data"""
    session = get_sync_session()
    
    try:
        # Get raw listing
        listing_raw = session.query(ListingRaw).filter_by(id=UUID(listing_raw_id)).first()
        
        if not listing_raw:
            logger.error(f"ListingRaw {listing_raw_id} not found")
            return
        
        # Get parser for source
        parser_class = PARSERS.get(listing_raw.source.name)
        if not parser_class:
            logger.error(f"No parser for source {listing_raw.source.name}")
            return
        
        # Parse HTML
        parsed_data = parser_class.parse(listing_raw.html_content, listing_raw.url)
        
        if not parsed_data:
            logger.error(f"Failed to parse listing {listing_raw_id}")
            listing_raw.parse_error = "Failed to extract structured data"
            session.commit()
            return
        
        # Check if normalized listing already exists
        existing = session.query(ListingNormalized).filter_by(
            listing_raw_id=listing_raw.id
        ).first()
        
        if existing:
            logger.info(f"Listing {listing_raw_id} already parsed, updating...")
            # Update existing
            for key, value in parsed_data.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            existing.updated_at = datetime.now(timezone.utc)
        else:
            # Create new normalized listing
            normalized = ListingNormalized(
                listing_raw_id=listing_raw.id,
                source_id=listing_raw.source_id,
                site_ad_id=listing_raw.site_ad_id,
                url=listing_raw.url,
                **parsed_data
            )
            session.add(normalized)
        
        # Mark as parsed
        listing_raw.parsed_at = datetime.now(timezone.utc)
        listing_raw.parse_error = None
        
        session.commit()
        
        logger.info(f"Successfully parsed listing {listing_raw_id}")
        
        # Trigger normalization
        if existing:
            normalize_listing.delay(str(existing.id))
        else:
            session.refresh(normalized)
            normalize_listing.delay(str(normalized.id))
        
        return {"status": "parsed", "listing_id": listing_raw_id}
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error parsing listing {listing_raw_id}: {e}", exc_info=True)
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
    
    finally:
        session.close()
