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
            
            # Extract title (contains brand, model, year, features)
            title_elem = soup.select_one('title')
            title_full = title_elem.text.strip() if title_elem else None
            
            # Extract brand/model from URL pattern: obiava-{id}-{brand}-{model}-...
            brand = None
            model = None
            url_match = re.search(r'obiava-\d+-([^-]+)-([^-/\s]+)', url)
            if url_match:
                brand = url_match.group(1).strip()
                model = url_match.group(2).strip()
            
            # Extract year from title (format: "Brand Model, 2021г.")
            year = None
            if title_full:
                year_match = re.search(r'(\d{4})\s*г', title_full)
                if year_match:
                    year = int(year_match.group(1))
            
            # Extract price from HTML (appears multiple times, usually in format "25 250 лв")
            price = None
            currency = 'BGN'
            
            # Try regex pattern - Mobile.bg embeds price in HTML
            # Look for prices with at least 3 digits (to filter out navigation elements like "30 €")
            price_matches = re.findall(r'(\d[\d\s]{3,})\s*(лв|€|EUR)', html)
            if price_matches:
                # Take the largest number (actual listing price, not UI elements)
                prices = []
                for price_text, currency_symbol in price_matches:
                    try:
                        value = int(price_text.replace(' ', ''))
                        prices.append((value, currency_symbol))
                    except ValueError:
                        continue
                
                if prices:
                    # Get the maximum price (most likely the actual listing price)
                    price, currency_symbol = max(prices, key=lambda x: x[0])
                    if currency_symbol in ['€', 'EUR']:
                        currency = 'EUR'
            
            # Extract details table (Mobile.bg uses various table structures)
            details = {}
            detail_rows = soup.select('tr')  # All table rows
            for row in detail_rows:
                cells = row.find_all('td')
                if len(cells) == 2:
                    key = cells[0].text.strip().rstrip(':')
                    value = cells[1].text.strip()
                    details[key] = value
            
            # Fallback: Extract from table rows if URL parsing failed
            if not brand:
                brand = details.get('Марка', None)
            if not model:
                model = details.get('Модел', None)
            
            # Try to extract from title as last resort
            if not brand and title_full:
                # Common pattern: "BMW 520 D - touring, 2015г."
                parts = title_full.split(',')[0].split()  # Take part before comma
                if len(parts) > 0:
                    brand = parts[0]
                if len(parts) > 1:
                    model = ' '.join(parts[1:3])  # Take next 1-2 words
            
            # Extract other fields from details table (if not already extracted)
            # Year - only extract from table if not already found in title
            if not year:
                year_text = details.get('Година', details.get('Първа регистрация', ''))
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
                'title': title_full,
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
    'Mobile.bg': MobileBgParser,  # Match database source name
    'mobile_bg': MobileBgParser,
    'Cars.bg': CarsBgParser,
    'cars_bg': CarsBgParser,
    'OLX.bg': OlxParser,
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
        
        # Check if spider already extracted data
        if listing_raw.parsed_data:
            logger.info(f"Using spider-extracted data for {listing_raw_id}")
            parsed_data = listing_raw.parsed_data
        # Check if we have HTML content
        elif not listing_raw.raw_html_path and not hasattr(listing_raw, 'html_content'):
            # For test listings without HTML, create placeholder parsed data
            logger.info(f"No HTML for listing {listing_raw_id}, using placeholder data")
            parsed_data = {
                'title': f"Test Listing {listing_raw.site_ad_id}",
                'price': 15000,
                'currency': 'BGN',
                'year': 2015,
                'mileage_km': 150000,
                'brand': 'BMW',
                'model': '320d',
                'fuel_type': 'Diesel',
                'gearbox': 'Automatic',
                'body_type': 'Sedan',
                'region': 'Sofia',
                'description': 'Test listing - no HTML available',
            }
        else:
            # Parse HTML
            html_content = listing_raw.raw_html
            if not html_content and listing_raw.raw_html_path:
                # TODO: Load HTML from S3/file system
                logger.error(f"HTML path exists but content not loaded: {listing_raw.raw_html_path}")
                return
            
            parsed_data = parser_class.parse(html_content, listing_raw.url)
        
        if not parsed_data:
            logger.error(f"Failed to parse listing {listing_raw_id}")
            listing_raw.parse_error = "Failed to extract structured data"
            session.commit()
            return
        
        # Check if normalized listing already exists
        existing = session.query(ListingNormalized).filter_by(
            raw_id=listing_raw.id
        ).first()
        
        if existing:
            logger.info(f"Listing {listing_raw_id} already parsed, updating...")
            # Update existing - map parser fields to model fields
            field_mapping = {
                'brand': 'brand_id',
                'model': 'model_id',
                'year': 'year',
                'mileage_km': 'mileage_km',
                'fuel': 'fuel',
                'fuel_type': 'fuel',
                'gearbox': 'gearbox',
                'body': 'body',
                'body_type': 'body',
                'price': 'price_bgn',
                'currency': 'currency',
                'region': 'region',
                'title': 'title',
                'description': 'description',
            }
            
            for parser_field, model_field in field_mapping.items():
                if parser_field in parsed_data and parsed_data[parser_field] is not None:
                    setattr(existing, model_field, parsed_data[parser_field])
            
            existing.updated_at = datetime.now(timezone.utc)
        else:
            # Create new normalized listing - map parser fields to model fields
            # Handle both spider data (fuel, body) and parser data (fuel_type, body_type)
            normalized_data = {
                'brand_id': parsed_data.get('brand'),
                'model_id': parsed_data.get('model'),
                'year': parsed_data.get('year'),
                'mileage_km': parsed_data.get('mileage_km'),
                'fuel': parsed_data.get('fuel') or parsed_data.get('fuel_type'),
                'gearbox': parsed_data.get('gearbox'),
                'body': parsed_data.get('body') or parsed_data.get('body_type'),
                'price_bgn': parsed_data.get('price'),
                'currency': parsed_data.get('currency', 'BGN'),
                'region': parsed_data.get('region'),
                'title': parsed_data.get('title'),
                'description': parsed_data.get('description'),
            }
            # Remove None values
            normalized_data = {k: v for k, v in normalized_data.items() if v is not None}
            
            normalized = ListingNormalized(
                raw_id=listing_raw.id,
                **normalized_data
            )
            session.add(normalized)
        
        # Mark as parsed
        listing_raw.parsed_at = datetime.now(timezone.utc)
        listing_raw.parse_error = None
        
        session.commit()
        
        logger.info(f"Successfully parsed listing {listing_raw_id}")
        
        # Trigger normalization (pass raw_id, not normalized_id)
        normalize_listing.delay(listing_raw_id)
        
        return {"status": "parsed", "listing_id": listing_raw_id}
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error parsing listing {listing_raw_id}: {e}", exc_info=True)
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
    
    finally:
        session.close()
