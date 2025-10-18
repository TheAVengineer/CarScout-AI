"""
Brand and model normalization utilities
"""
import re
from typing import Optional, Tuple

from libs.domain.database import get_sync_session
from libs.domain.models import BrandModel


class BrandModelNormalizer:
    """Normalize brand and model names using mapping table"""
    
    def __init__(self):
        self.session = get_sync_session()
        self._cache = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load all brand/model mappings into memory"""
        mappings = self.session.query(BrandModel).filter_by(active=True).all()
        for mapping in mappings:
            key = f"{mapping.brand.lower()}_{mapping.model.lower()}"
            self._cache[key] = (mapping.normalized_brand, mapping.normalized_model)
            
            # Also cache aliases
            for alias in (mapping.aliases or []):
                alias_key = f"{mapping.brand.lower()}_{alias.lower()}"
                self._cache[alias_key] = (mapping.normalized_brand, mapping.normalized_model)
    
    def normalize(self, brand: str, model: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Normalize brand and model names
        
        Args:
            brand: Raw brand name
            model: Raw model name
            
        Returns:
            Tuple of (normalized_brand, normalized_model)
        """
        if not brand or not model:
            return None, None
        
        # Clean inputs
        brand_clean = self._clean_text(brand)
        model_clean = self._clean_text(model)
        
        # Check cache
        key = f"{brand_clean}_{model_clean}"
        if key in self._cache:
            return self._cache[key]
        
        # Try fuzzy matching
        return self._fuzzy_match(brand_clean, model_clean)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters
        text = re.sub(r'[^\w\s-]', '', text)
        
        return text
    
    def _fuzzy_match(self, brand: str, model: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Attempt fuzzy matching for unknown brand/model combinations
        """
        # Try matching just the brand
        for key, (norm_brand, norm_model) in self._cache.items():
            cached_brand, cached_model = key.split('_', 1)
            
            if brand == cached_brand:
                # Brand matches, check if model is similar
                if self._is_similar(model, cached_model):
                    return norm_brand, norm_model
        
        return None, None
    
    def _is_similar(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """Check if two strings are similar using simple character overlap"""
        if not text1 or not text2:
            return False
        
        # Simple Jaccard similarity
        set1 = set(text1.split())
        set2 = set(text2.split())
        
        if not set1 or not set2:
            return False
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        similarity = intersection / union if union > 0 else 0
        return similarity >= threshold


class FieldNormalizer:
    """Normalize various listing fields"""
    
    # Fuel type mappings
    FUEL_MAPPINGS = {
        'дизел': 'diesel',
        'diesel': 'diesel',
        'бензин': 'petrol',
        'petrol': 'petrol',
        'gasoline': 'petrol',
        'газ': 'lpg',
        'lpg': 'lpg',
        'cng': 'cng',
        'електро': 'electric',
        'electric': 'electric',
        'хибрид': 'hybrid',
        'hybrid': 'hybrid',
    }
    
    # Gearbox mappings
    GEARBOX_MAPPINGS = {
        'автоматична': 'automatic',
        'automatic': 'automatic',
        'auto': 'automatic',
        'ръчна': 'manual',
        'manual': 'manual',
        'полуавтоматична': 'semi-automatic',
        'semi-automatic': 'semi-automatic',
    }
    
    # Body type mappings
    BODY_MAPPINGS = {
        'седан': 'sedan',
        'sedan': 'sedan',
        'хечбек': 'hatchback',
        'hatchback': 'hatchback',
        'комби': 'wagon',
        'wagon': 'wagon',
        'estate': 'wagon',
        'джип': 'suv',
        'suv': 'suv',
        'кабрио': 'convertible',
        'convertible': 'convertible',
        'купе': 'coupe',
        'coupe': 'coupe',
        'ван': 'van',
        'van': 'van',
        'пикап': 'pickup',
        'pickup': 'pickup',
    }
    
    @classmethod
    def normalize_fuel(cls, fuel: Optional[str]) -> Optional[str]:
        """Normalize fuel type"""
        if not fuel:
            return None
        
        fuel_lower = fuel.lower().strip()
        return cls.FUEL_MAPPINGS.get(fuel_lower)
    
    @classmethod
    def normalize_gearbox(cls, gearbox: Optional[str]) -> Optional[str]:
        """Normalize gearbox type"""
        if not gearbox:
            return None
        
        gearbox_lower = gearbox.lower().strip()
        return cls.GEARBOX_MAPPINGS.get(gearbox_lower)
    
    @classmethod
    def normalize_body(cls, body: Optional[str]) -> Optional[str]:
        """Normalize body type"""
        if not body:
            return None
        
        body_lower = body.lower().strip()
        return cls.BODY_MAPPINGS.get(body_lower)
    
    @classmethod
    def normalize_mileage(cls, mileage: Optional[int]) -> Optional[int]:
        """Normalize mileage (ensure it's reasonable)"""
        if mileage is None:
            return None
        
        # Remove obviously wrong values
        if mileage < 0 or mileage > 1_000_000:
            return None
        
        return mileage
    
    @classmethod
    def normalize_year(cls, year: Optional[int]) -> Optional[int]:
        """Normalize year (ensure it's reasonable)"""
        if year is None:
            return None
        
        current_year = 2024
        if year < 1900 or year > current_year + 1:
            return None
        
        return year
    
    @classmethod
    def convert_price_to_bgn(cls, price: Optional[float], currency: str = 'BGN') -> Optional[float]:
        """Convert price to BGN"""
        if price is None:
            return None
        
        # Currency conversion rates (approximate)
        rates = {
            'BGN': 1.0,
            'EUR': 1.96,
            'USD': 1.80,
        }
        
        rate = rates.get(currency.upper(), 1.0)
        return round(price * rate, 2)


# Initialize default brand/model mappings
def seed_brand_models():
    """Seed the database with common brand/model mappings"""
    session = get_sync_session()
    
    common_mappings = [
        # BMW
        ('BMW', 'X5', 'bmw', 'x5', ['x 5', 'х5']),
        ('BMW', '320', 'bmw', '320', ['3 series', '3-series']),
        ('BMW', '520', 'bmw', '520', ['5 series', '5-series']),
        
        # Mercedes
        ('Mercedes', 'C-Class', 'mercedes-benz', 'c-class', ['c class', 'c-klasse']),
        ('Mercedes', 'E-Class', 'mercedes-benz', 'e-class', ['e class', 'e-klasse']),
        ('Mercedes', 'S-Class', 'mercedes-benz', 's-class', ['s class', 's-klasse']),
        
        # Audi
        ('Audi', 'A4', 'audi', 'a4', ['а4']),
        ('Audi', 'A6', 'audi', 'a6', ['а6']),
        ('Audi', 'Q5', 'audi', 'q5', ['q 5']),
        
        # Volkswagen
        ('VW', 'Golf', 'volkswagen', 'golf', ['голф']),
        ('VW', 'Passat', 'volkswagen', 'passat', ['пасат']),
        ('VW', 'Tiguan', 'volkswagen', 'tiguan', ['тигуан']),
        
        # Ford
        ('Ford', 'Focus', 'ford', 'focus', ['фокус']),
        ('Ford', 'Fiesta', 'ford', 'fiesta', ['фиеста']),
        
        # Toyota
        ('Toyota', 'Corolla', 'toyota', 'corolla', ['корола']),
        ('Toyota', 'Yaris', 'toyota', 'yaris', ['ярис']),
        ('Toyota', 'RAV4', 'toyota', 'rav4', ['rav 4']),
    ]
    
    for brand, model, norm_brand, norm_model, aliases in common_mappings:
        existing = session.query(BrandModel).filter_by(
            normalized_brand=norm_brand,
            normalized_model=norm_model
        ).first()
        
        if not existing:
            mapping = BrandModel(
                brand=brand,
                model=model,
                normalized_brand=norm_brand,
                normalized_model=norm_model,
                aliases=aliases,
                locale='bg',
                active=True,
            )
            session.add(mapping)
    
    session.commit()
    session.close()
