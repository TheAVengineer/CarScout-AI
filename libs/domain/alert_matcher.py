"""
Alert matching engine with DSL query parser
"""
import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from libs.domain.models import Alert, ListingNormalized, User, Plan

logger = logging.getLogger(__name__)


class AlertQueryParser:
    """Parse user alert queries in DSL format"""
    
    # DSL examples:
    # "BMW X5 diesel <25000 2016+ <180000km automatic"
    # "Audi A4 petrol 2018+ Sofia <15000"
    # "Mercedes C-Class 2015-2020 >180hp sedan"
    
    FUEL_TYPES = {
        'diesel': 'diesel',
        'дизел': 'diesel',
        'petrol': 'petrol',
        'benzin': 'petrol',
        'бензин': 'petrol',
        'gasoline': 'petrol',
        'hybrid': 'hybrid',
        'хибрид': 'hybrid',
        'electric': 'electric',
        'електрически': 'electric',
        'lpg': 'lpg',
        'газ': 'lpg',
    }
    
    GEARBOX_TYPES = {
        'automatic': 'automatic',
        'автоматична': 'automatic',
        'auto': 'automatic',
        'manual': 'manual',
        'ръчна': 'manual',
    }
    
    BODY_TYPES = {
        'sedan': 'sedan',
        'седан': 'sedan',
        'hatchback': 'hatchback',
        'хечбек': 'hatchback',
        'suv': 'suv',
        'джип': 'suv',
        'wagon': 'wagon',
        'комби': 'wagon',
        'coupe': 'coupe',
        'купе': 'coupe',
        'convertible': 'convertible',
        'кабрио': 'convertible',
        'van': 'van',
        'ван': 'van',
        'pickup': 'pickup',
    }
    
    def parse(self, query: str) -> Dict[str, Any]:
        """
        Parse DSL query into structured filters
        
        Returns:
            Dict with filters: {
                'brand': str,
                'model': str,
                'price_max': int,
                'price_min': int,
                'year_min': int,
                'year_max': int,
                'mileage_max': int,
                'fuel_type': str,
                'gearbox': str,
                'body_type': str,
                'region': str,
                'power_min': int,
            }
        """
        query = query.lower().strip()
        filters = {}
        
        # Extract brand (first word, usually capitalized in original)
        words = query.split()
        if words:
            # Brand is typically the first word
            filters['brand'] = words[0].capitalize()
            
            # Model might be next 1-2 words before filters
            model_words = []
            for i in range(1, min(4, len(words))):
                word = words[i]
                # Stop if we hit a filter pattern
                if any(c in word for c in ['<', '>', '+', '-']) or \
                   word in self.FUEL_TYPES or \
                   word in self.GEARBOX_TYPES or \
                   word.isdigit():
                    break
                model_words.append(word)
            
            if model_words:
                filters['model'] = ' '.join(model_words).title()
        
        # Extract price filters
        # Pattern: <25000 or >15000
        price_patterns = re.findall(r'([<>])(\d+)(?!km|hp)', query)
        for operator, value in price_patterns:
            value = int(value)
            if operator == '<':
                filters['price_max'] = value
            elif operator == '>':
                filters['price_min'] = value
        
        # Extract year filters
        # Pattern: 2016+ or 2015-2020
        year_range = re.search(r'(\d{4})-(\d{4})', query)
        if year_range:
            filters['year_min'] = int(year_range.group(1))
            filters['year_max'] = int(year_range.group(2))
        else:
            year_min = re.search(r'(\d{4})\+', query)
            if year_min:
                filters['year_min'] = int(year_min.group(1))
        
        # Extract mileage filter
        # Pattern: <180000km or <180km
        mileage = re.search(r'<(\d+)\s*km', query)
        if mileage:
            filters['mileage_max'] = int(mileage.group(1))
            # Handle thousands
            if filters['mileage_max'] < 1000:
                filters['mileage_max'] *= 1000
        
        # Extract power filter
        # Pattern: >180hp
        power = re.search(r'>(\d+)\s*hp', query)
        if power:
            filters['power_min'] = int(power.group(1))
        
        # Extract fuel type
        for fuel_key, fuel_value in self.FUEL_TYPES.items():
            if fuel_key in query:
                filters['fuel_type'] = fuel_value
                break
        
        # Extract gearbox
        for gearbox_key, gearbox_value in self.GEARBOX_TYPES.items():
            if gearbox_key in query:
                filters['gearbox'] = gearbox_value
                break
        
        # Extract body type
        for body_key, body_value in self.BODY_TYPES.items():
            if body_key in query:
                filters['body_type'] = body_value
                break
        
        # Extract region (common Bulgarian cities)
        cities = ['sofia', 'софия', 'plovdiv', 'пловдив', 'varna', 'варна', 
                 'burgas', 'бургас', 'ruse', 'русе', 'stara zagora']
        for city in cities:
            if city in query:
                filters['region'] = city.title()
                break
        
        return filters


class AlertMatcher:
    """Match listings against user alerts"""
    
    def __init__(self, session):
        self.session = session
        self.parser = AlertQueryParser()
    
    def matches(self, listing: ListingNormalized, alert: Alert) -> bool:
        """Check if listing matches alert criteria"""
        
        # Parse alert query
        filters = self.parser.parse(alert.query)
        
        # Check each filter
        if 'brand' in filters:
            if not listing.normalized_brand:
                return False
            if listing.normalized_brand.lower() != filters['brand'].lower():
                return False
        
        if 'model' in filters:
            if not listing.normalized_model:
                return False
            # Partial match (e.g., "X5" matches "X5 xDrive")
            if filters['model'].lower() not in listing.normalized_model.lower():
                return False
        
        if 'price_max' in filters:
            if not listing.price_bgn or listing.price_bgn > filters['price_max']:
                return False
        
        if 'price_min' in filters:
            if not listing.price_bgn or listing.price_bgn < filters['price_min']:
                return False
        
        if 'year_min' in filters:
            if not listing.year or listing.year < filters['year_min']:
                return False
        
        if 'year_max' in filters:
            if not listing.year or listing.year > filters['year_max']:
                return False
        
        if 'mileage_max' in filters:
            if not listing.mileage_km or listing.mileage_km > filters['mileage_max']:
                return False
        
        if 'fuel_type' in filters:
            if not listing.normalized_fuel or listing.normalized_fuel != filters['fuel_type']:
                return False
        
        if 'gearbox' in filters:
            if not listing.normalized_gearbox or listing.normalized_gearbox != filters['gearbox']:
                return False
        
        if 'body_type' in filters:
            if not listing.normalized_body or listing.normalized_body != filters['body_type']:
                return False
        
        if 'region' in filters:
            if not listing.region or filters['region'].lower() not in listing.region.lower():
                return False
        
        if 'power_min' in filters:
            if not listing.engine_power_hp or listing.engine_power_hp < filters['power_min']:
                return False
        
        # All filters passed
        return True
    
    def find_matching_alerts(self, listing: ListingNormalized) -> List[Alert]:
        """Find all alerts that match this listing"""
        
        # Get all active alerts
        active_alerts = self.session.query(Alert).join(User).filter(
            Alert.is_active == True,
        ).all()
        
        matching = []
        
        for alert in active_alerts:
            try:
                if self.matches(listing, alert):
                    matching.append(alert)
            except Exception as e:
                logger.error(f"Error matching alert {alert.id}: {e}")
        
        return matching
    
    def should_notify_user(self, user: User, alert: Alert, listing: ListingNormalized) -> bool:
        """
        Check if user should be notified based on plan limits
        
        Returns:
            True if notification should be sent, False otherwise
        """
        from datetime import timedelta
        from libs.domain.models import AlertMatch
        
        # Get user's plan
        plan = user.plan
        
        if not plan:
            logger.warning(f"User {user.id} has no plan")
            return False
        
        # Check delay requirement
        delay_minutes = plan.limits.get('delay_minutes', 0)
        if delay_minutes > 0:
            # Check if listing is old enough
            age_minutes = (datetime.now(timezone.utc) - listing.created_at).total_seconds() / 60
            if age_minutes < delay_minutes:
                logger.info(f"Listing too fresh for user {user.id} (delay: {delay_minutes}min)")
                return False
        
        # Check daily cap
        daily_cap = plan.limits.get('daily_alert_cap', 999)
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        today_count = self.session.query(AlertMatch).filter(
            AlertMatch.alert_id == alert.id,
            AlertMatch.created_at >= today_start,
            AlertMatch.notified == True,
        ).count()
        
        if today_count >= daily_cap:
            logger.info(f"Daily cap reached for alert {alert.id} ({today_count}/{daily_cap})")
            return False
        
        return True
