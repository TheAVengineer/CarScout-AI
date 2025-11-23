"""
Simple Rating System for New Car Listings
==========================================

Focus: Clear, transparent scoring without complex ML models.
Target: New listings (last 2 days) for real-time deal detection.

Scoring Components (0-10 scale):
1. Price/Value Ratio (40% weight) - Is it priced well?
2. Vehicle Age (20% weight) - Newer is better
3. Mileage (20% weight) - Lower is better  
4. Listing Quality (10% weight) - Description, photos
5. Freshness Bonus (10% weight) - How new is the listing?

Example Scores:
- 9.0-10.0: EXCELLENT deal (post immediately)
- 8.0-8.9:  GREAT deal (post with high priority)
- 7.0-7.9:  GOOD deal (post if channel quiet)
- 6.0-6.9:  DECENT deal (maybe post)
- <6.0:     SKIP (not worth posting)
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class SimpleRatingEngine:
    """Simple, transparent rating system for car listings"""
    
    def __init__(
        self,
        posting_threshold: float = 8.0,  # Only post excellent deals
        min_price: int = 5000,           # Skip very cheap cars (likely problems)
        max_price: int = 100000,         # Skip luxury cars (different market)
        min_year: int = 2015,            # Skip older cars
        max_mileage: int = 150000,       # Skip high-mileage cars
    ):
        self.posting_threshold = posting_threshold
        self.min_price = min_price
        self.max_price = max_price
        self.min_year = min_year
        self.max_mileage = max_mileage
    
    def rate_listing(
        self,
        price_bgn: int,
        year: int,
        mileage_km: Optional[int],
        brand: str,
        model: str,
        fuel_type: Optional[str],
        description_length: int,
        image_count: int,
        created_at: datetime,
    ) -> Dict[str, Any]:
        """
        Rate a car listing with simple, transparent criteria.
        
        Returns:
            {
                'score': 8.5,
                'should_post': True,
                'components': {
                    'price_score': 4.0,
                    'age_score': 1.8,
                    'mileage_score': 1.7,
                    'quality_score': 0.9,
                    'freshness_score': 0.1
                },
                'reasons': ['Excellent price point', 'Recent year', ...],
                'warnings': ['High mileage', ...]
            }
        """
        reasons = []
        warnings = []
        
        # Pre-filters (automatic rejection)
        if not self._passes_filters(price_bgn, year, mileage_km):
            return {
                'score': 0.0,
                'should_post': False,
                'reasons': [],
                'warnings': ['Filtered out: price, year, or mileage outside acceptable range']
            }
        
        # 1. Price/Value Score (0-4 points, 40% of total)
        price_score = self._calculate_price_score(price_bgn, year, brand)
        
        # 2. Age Score (0-2 points, 20% of total)
        age_score = self._calculate_age_score(year)
        
        # 3. Mileage Score (0-2 points, 20% of total)
        mileage_score = self._calculate_mileage_score(mileage_km, year)
        
        # 4. Quality Score (0-1 points, 10% of total)
        quality_score = self._calculate_quality_score(description_length, image_count)
        
        # 5. Freshness Score (0-1 points, 10% of total)
        freshness_score = self._calculate_freshness_score(created_at)
        
        # Calculate total (0-10 scale)
        total_score = price_score + age_score + mileage_score + quality_score + freshness_score
        total_score = min(10.0, max(0.0, total_score))
        
        # Generate reasons
        reasons = self._generate_reasons(
            price_bgn, year, mileage_km, brand, model, 
            price_score, age_score, mileage_score, quality_score
        )
        
        # Generate warnings
        warnings = self._generate_warnings(year, mileage_km, price_bgn, description_length)
        
        # Should we post?
        should_post = total_score >= self.posting_threshold and len(warnings) == 0
        
        return {
            'score': round(total_score, 2),
            'should_post': should_post,
            'components': {
                'price_score': round(price_score, 2),
                'age_score': round(age_score, 2),
                'mileage_score': round(mileage_score, 2),
                'quality_score': round(quality_score, 2),
                'freshness_score': round(freshness_score, 2),
            },
            'reasons': reasons,
            'warnings': warnings,
        }
    
    def _passes_filters(self, price: int, year: int, mileage: Optional[int]) -> bool:
        """Basic filters to skip bad listings"""
        if price < self.min_price or price > self.max_price:
            return False
        if year < self.min_year:
            return False
        if mileage and mileage > self.max_mileage:
            return False
        return True
    
    def _calculate_price_score(self, price: int, year: int, brand: str) -> float:
        """
        Score based on price/value ratio.
        Uses simple heuristics instead of ML models.
        
        Logic:
        - Premium brands (Mercedes, BMW, Audi) should be priced higher
        - Newer cars should be more expensive
        - Sweet spot: 10,000-30,000 BGN for 2015-2020 cars
        """
        # Expected price range based on year (rough estimate)
        current_year = datetime.now().year
        age = current_year - year
        
        # Premium brands have 20% higher expected prices
        premium_brands = ['mercedes-benz', 'bmw', 'audi', 'lexus', 'porsche']
        is_premium = brand.lower() in premium_brands
        
        # Base expected price by age
        if age <= 3:
            expected_min = 25000 if is_premium else 18000
            expected_max = 50000 if is_premium else 35000
        elif age <= 5:
            expected_min = 18000 if is_premium else 12000
            expected_max = 35000 if is_premium else 25000
        elif age <= 8:
            expected_min = 12000 if is_premium else 8000
            expected_max = 25000 if is_premium else 18000
        else:
            expected_min = 6000 if is_premium else 5000
            expected_max = 15000 if is_premium else 12000
        
        # Score based on how well-priced it is
        if price < expected_min:
            return 4.0  # Very cheap! Could be great deal or problem car
        elif price <= expected_max * 0.7:
            return 3.5  # Below average price (good deal)
        elif price <= expected_max:
            return 2.5  # Fair price
        elif price <= expected_max * 1.2:
            return 1.5  # Slightly expensive
        else:
            return 0.5  # Too expensive
    
    def _calculate_age_score(self, year: int) -> float:
        """Score based on vehicle age (0-2 points)"""
        current_year = datetime.now().year
        age = current_year - year
        
        if age <= 2:
            return 2.0  # Nearly new
        elif age <= 4:
            return 1.8  # Very recent
        elif age <= 6:
            return 1.5  # Recent
        elif age <= 8:
            return 1.2  # Decent age
        else:
            return 0.8  # Older car
    
    def _calculate_mileage_score(self, mileage: Optional[int], year: int) -> float:
        """Score based on mileage relative to age (0-2 points)"""
        if not mileage:
            return 1.0  # Neutral if unknown
        
        current_year = datetime.now().year
        age = current_year - year
        
        # Expected mileage: ~15,000 km/year
        expected_mileage = age * 15000
        
        if mileage < expected_mileage * 0.5:
            return 2.0  # Very low mileage!
        elif mileage < expected_mileage * 0.8:
            return 1.7  # Low mileage
        elif mileage < expected_mileage * 1.2:
            return 1.3  # Average mileage
        elif mileage < expected_mileage * 1.5:
            return 0.8  # Above average
        else:
            return 0.3  # High mileage
    
    def _calculate_quality_score(self, description_length: int, image_count: int) -> float:
        """Score based on listing quality (0-1 points)"""
        score = 0.0
        
        # Description quality (0-0.5)
        if description_length > 500:
            score += 0.5  # Detailed description
        elif description_length > 200:
            score += 0.3  # Decent description
        elif description_length > 50:
            score += 0.1  # Minimal description
        
        # Photo quality (0-0.5)
        if image_count >= 10:
            score += 0.5  # Many photos
        elif image_count >= 5:
            score += 0.3  # Several photos
        elif image_count >= 2:
            score += 0.1  # Few photos
        
        return score
    
    def _calculate_freshness_score(self, created_at: datetime) -> float:
        """Score based on how new the listing is (0-1 points)"""
        now = datetime.now(timezone.utc)
        if not created_at.tzinfo:
            created_at = created_at.replace(tzinfo=timezone.utc)
        
        age_hours = (now - created_at).total_seconds() / 3600
        
        if age_hours <= 1:
            return 1.0  # Posted in last hour!
        elif age_hours <= 6:
            return 0.7  # Very fresh
        elif age_hours <= 24:
            return 0.4  # Today
        elif age_hours <= 48:
            return 0.2  # Yesterday
        else:
            return 0.0  # Older
    
    def _generate_reasons(
        self,
        price: int,
        year: int,
        mileage: Optional[int],
        brand: str,
        model: str,
        price_score: float,
        age_score: float,
        mileage_score: float,
        quality_score: float,
    ) -> list[str]:
        """Generate human-readable reasons for the score"""
        reasons = []
        
        # Price
        if price_score >= 3.5:
            reasons.append(f"💰 Excellent price: {price:,} BGN")
        elif price_score >= 2.5:
            reasons.append(f"💵 Fair price: {price:,} BGN")
        
        # Age
        if age_score >= 1.8:
            reasons.append(f"📅 Recent year: {year}")
        
        # Mileage
        if mileage_score >= 1.7:
            km_str = f"{mileage:,} км" if mileage else "N/A"
            reasons.append(f"🚗 Low mileage: {km_str}")
        
        # Quality
        if quality_score >= 0.8:
            reasons.append("📝 Well-documented listing")
        
        # Brand
        premium_brands = ['mercedes-benz', 'bmw', 'audi', 'lexus', 'porsche']
        if brand.lower() in premium_brands:
            reasons.append(f"⭐ Premium brand: {brand.title()}")
        
        return reasons
    
    def _generate_warnings(
        self,
        year: int,
        mileage: Optional[int],
        price: int,
        description_length: int,
    ) -> list[str]:
        """Generate warnings for potential red flags"""
        warnings = []
        
        # Very cheap (could indicate problems)
        if price < 8000:
            warnings.append("⚠️ Very low price - verify condition")
        
        # High mileage
        if mileage and mileage > 200000:
            warnings.append("⚠️ High mileage - check maintenance history")
        
        # Minimal description (seller hiding something?)
        if description_length < 50:
            warnings.append("⚠️ Minimal description - request more details")
        
        return warnings
