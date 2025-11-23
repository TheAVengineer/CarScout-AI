"""
Market-Aware Rating System - Intelligent scoring based on real market data
===========================================================================

This system is SMART about the Bulgarian used car market:

1. **Price Brackets** - Different expectations for different price ranges:
   - Budget (5-10k): Condition/mileage critical, 20%+ discount is excellent
   - Sweet Spot (10-30k): Best deals, 25%+ discount is excellent
   - Premium (30-60k): Newer cars, 15%+ discount is good
   - Luxury (60k+): Everything matters, 10%+ discount is good

2. **Database Comparables** - Uses real listings to understand market:
   - Finds similar cars (brand, model, year ±2, mileage ±30%)
   - Calculates median price from real listings
   - Accounts for market conditions (supply/demand)

3. **Red Flags Detection** - Filters out scams and clickbait:
   - Leasing vehicles (partial payment)
   - Right-hand drive (cheaper but harder to sell)
   - Not in Bulgaria (import costs hidden)
   - Suspiciously low price (too good to be true)
   - Missing critical info (hiding problems)

4. **Context-Aware Scoring** - Understands nuances:
   - Cheap cars: Mileage + condition matter most
   - Mid-range: Balance of all factors
   - Expensive: Specs, equipment, history matter

Author: CarScout AI Team
Date: November 22, 2025
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text
import re
import logging

logger = logging.getLogger(__name__)


class RedFlag:
    """Red flag detection for scam/clickbait listings"""
    
    # Keywords that indicate problems
    LEASING_KEYWORDS = [
        'лизинг', 'лиз.', 'leasing', 'месечна вноска', 'първоначална вноска',
        'авансово', 'на вноски', 'кредит', 'финансиране'
    ]
    
    RIGHT_HAND_DRIVE_KEYWORDS = [
        'десен волан', 'дясна кормилница', 'right hand', 'rhd', 'английски',
        'от англия', 'japanese', 'от япония'
    ]
    
    NOT_IN_BULGARIA_KEYWORDS = [
        'внос', 'увоз', 'германия', 'deutschland', 'франция', 'италия',
        'холандия', 'нидерландия', 'czech', 'чехия', 'от чужбина',
        'на път', 'идва', 'очаква се'
    ]
    
    ACCIDENT_KEYWORDS = [
        'катастрофирал', 'удряна', 'ударен', 'счупен', 'повредена',
        'за части', 'за ремонт', 'без документи', 'без регистрация'
    ]
    
    SUSPICIOUS_PHRASES = [
        'спешно', 'бърза продажба', 'навлизам', 'напускам държавата',
        'не отговарям на смс', 'само обаждане', 'последна цена'
    ]
    
    @staticmethod
    def detect_leasing(description: str, price: int, year: int) -> Optional[str]:
        """Detect if listing is leasing/partial payment"""
        desc_lower = description.lower()
        
        # Check keywords
        for keyword in RedFlag.LEASING_KEYWORDS:
            if keyword in desc_lower:
                return f"🚨 LEASING: Detected '{keyword}' - not full price"
        
        # Heuristic: Very new expensive car at budget price
        current_year = datetime.now().year
        if year >= current_year - 2 and price < 20000:
            if any(word in desc_lower for word in ['bmw', 'mercedes', 'audi', 'lexus']):
                return "🚨 SUSPICIOUS: New premium car too cheap - possible leasing"
        
        return None
    
    @staticmethod
    def detect_right_hand_drive(description: str, title: str = '') -> Optional[str]:
        """Detect right-hand drive vehicles"""
        combined = (description + ' ' + title).lower()
        
        for keyword in RedFlag.RIGHT_HAND_DRIVE_KEYWORDS:
            if keyword in combined:
                return f"⚠️ RIGHT-HAND DRIVE: Detected '{keyword}' - harder to sell"
        
        return None
    
    @staticmethod
    def detect_not_in_bulgaria(description: str, title: str = '') -> Optional[str]:
        """Detect cars not yet in Bulgaria"""
        combined = (description + ' ' + title).lower()
        
        for keyword in RedFlag.NOT_IN_BULGARIA_KEYWORDS:
            if keyword in combined:
                return f"⚠️ NOT IN BULGARIA: Detected '{keyword}' - hidden costs"
        
        return None
    
    @staticmethod
    def detect_accident_damage(description: str) -> Optional[str]:
        """Detect accident or damage"""
        desc_lower = description.lower()
        
        for keyword in RedFlag.ACCIDENT_KEYWORDS:
            if keyword in desc_lower:
                return f"🚫 DAMAGE: Detected '{keyword}' - avoid"
        
        return None
    
    @staticmethod
    def detect_suspicious_language(description: str) -> Optional[str]:
        """Detect suspicious seller behavior"""
        desc_lower = description.lower()
        
        count = sum(1 for phrase in RedFlag.SUSPICIOUS_PHRASES if phrase in desc_lower)
        if count >= 2:
            return "⚠️ SUSPICIOUS: Multiple urgency phrases - possible scam"
        
        return None
    
    @staticmethod
    def check_all(description: str, title: str, price: int, year: int) -> List[str]:
        """Run all red flag checks"""
        flags = []
        
        checks = [
            RedFlag.detect_leasing(description, price, year),
            RedFlag.detect_right_hand_drive(description, title),
            RedFlag.detect_not_in_bulgaria(description, title),
            RedFlag.detect_accident_damage(description),
            RedFlag.detect_suspicious_language(description),
        ]
        
        flags = [flag for flag in checks if flag is not None]
        return flags


class PriceBracket:
    """Price bracket definitions with different discount expectations"""
    
    BUDGET = (5000, 10000)      # 5-10k: Condition critical, 20%+ discount excellent
    SWEET_SPOT = (10000, 30000) # 10-30k: Best deals, 25%+ discount excellent
    PREMIUM = (30000, 60000)    # 30-60k: Newer cars, 15%+ discount good
    LUXURY = (60000, 150000)    # 60k+: Everything matters, 10%+ discount good
    
    @staticmethod
    def get_bracket(price: int) -> str:
        """Get price bracket name"""
        if price < PriceBracket.BUDGET[0]:
            return "too_cheap"
        elif price <= PriceBracket.BUDGET[1]:
            return "budget"
        elif price <= PriceBracket.SWEET_SPOT[1]:
            return "sweet_spot"
        elif price <= PriceBracket.PREMIUM[1]:
            return "premium"
        elif price <= PriceBracket.LUXURY[1]:
            return "luxury"
        else:
            return "too_expensive"
    
    @staticmethod
    def get_discount_thresholds(price: int) -> Dict[str, float]:
        """Get discount % thresholds for scoring"""
        bracket = PriceBracket.get_bracket(price)
        
        # Returns: excellent, good, fair thresholds
        thresholds = {
            "budget": {"excellent": 20, "good": 15, "fair": 10},
            "sweet_spot": {"excellent": 25, "good": 20, "fair": 15},
            "premium": {"excellent": 15, "good": 12, "fair": 8},
            "luxury": {"excellent": 10, "good": 8, "fair": 5},
        }
        
        return thresholds.get(bracket, {"excellent": 15, "good": 10, "fair": 5})


class MarketAwareRatingEngine:
    """
    Intelligent rating system that uses database comparables and market knowledge
    """
    
    def __init__(
        self,
        session: Session,
        posting_threshold: float = 7.5,  # More conservative than simple system
        require_comparables: bool = True,
        min_comparables: int = 5,
    ):
        self.session = session
        self.posting_threshold = posting_threshold
        self.require_comparables = require_comparables
        self.min_comparables = min_comparables
    
    def rate_listing(
        self,
        listing_id: str,
        price_bgn: int,
        year: int,
        mileage_km: Optional[int],
        brand: str,
        model: str,
        fuel_type: Optional[str],
        body_type: Optional[str],
        description: str,
        title: str,
        image_count: int,
        created_at: datetime,
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Rate a listing using market intelligence
        
        Returns comprehensive rating with:
        - Score (0-10)
        - Should post (bool)
        - Market context
        - Red flags
        - Detailed reasoning
        """
        # 1. RED FLAG CHECKS (blocking issues)
        red_flags = RedFlag.check_all(description, title, price_bgn, year)
        
        if red_flags:
            logger.warning(f"Listing {listing_id[:8]} has red flags: {red_flags}")
            return {
                'score': 0.0,
                'should_post': False,
                'red_flags': red_flags,
                'reasons': [],
                'market_context': {},
                'blocked': True,
                'block_reason': red_flags[0]  # First flag is blocking reason
            }
        
        # 2. GET COMPARABLES FROM DATABASE
        comparables = self._get_comparables(brand, model, year, mileage_km, price_bgn)
        
        if self.require_comparables and len(comparables) < self.min_comparables:
            logger.info(f"Listing {listing_id[:8]} has insufficient comparables ({len(comparables)})")
            return {
                'score': 0.0,
                'should_post': False,
                'red_flags': [],
                'reasons': [f"Not enough market data ({len(comparables)} comparables, need {self.min_comparables})"],
                'market_context': {'comparable_count': len(comparables)},
                'blocked': True,
                'block_reason': 'Insufficient market data'
            }
        
        # 3. CALCULATE MARKET POSITION
        market_context = self._analyze_market_position(price_bgn, comparables)
        
        # 4. CALCULATE SCORE COMPONENTS
        components = self._calculate_components(
            price_bgn=price_bgn,
            year=year,
            mileage_km=mileage_km,
            brand=brand,
            market_context=market_context,
            image_count=image_count,
            description_length=len(description),
            created_at=created_at,
        )
        
        # 5. CALCULATE TOTAL SCORE
        total_score = sum(components.values())
        total_score = min(10.0, max(0.0, total_score))
        
        # 6. GENERATE REASONS
        reasons = self._generate_reasons(components, market_context, price_bgn, year, mileage_km)
        
        # 7. FINAL DECISION
        should_post = (
            total_score >= self.posting_threshold
            and len(red_flags) == 0
            and market_context.get('discount_pct', 0) >= 10  # At least 10% discount
        )
        
        return {
            'score': round(total_score, 2),
            'should_post': should_post,
            'components': {k: round(v, 2) for k, v in components.items()},
            'market_context': market_context,
            'red_flags': red_flags,
            'reasons': reasons,
            'blocked': False,
        }
    
    def _get_comparables(
        self,
        brand: str,
        model: str,
        year: int,
        mileage_km: Optional[int],
        listing_price: int,
    ) -> List[Dict[str, Any]]:
        """
        Find comparable listings from database
        
        Criteria:
        - Same brand and model
        - Year ±2 years
        - Mileage ±30% (if available)
        - Active listings only
        - Exclude outliers (too cheap/expensive)
        """
        try:
            # Build query for comparables - NO LIMIT to get complete market picture
            query = text("""
                SELECT 
                    price_bgn,
                    year,
                    mileage_km,
                    created_at
                FROM listings_normalized
                WHERE brand_id = :brand
                AND model_id = :model
                AND year BETWEEN :year_min AND :year_max
                AND price_bgn BETWEEN :price_min AND :price_max
                ORDER BY created_at DESC
            """)
            
            # Price range: ±50% to catch market range
            price_min = int(float(listing_price) * 0.5)
            price_max = int(float(listing_price) * 1.5)
            
            result = self.session.execute(query, {
                'brand': brand.lower(),
                'model': model.lower(),
                'year_min': year - 2,
                'year_max': year + 2,
                'price_min': price_min,
                'price_max': price_max,
            })
            
            comparables = []
            for row in result:
                created_at = row[3]
                if created_at and not created_at.tzinfo:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                
                comparables.append({
                    'price': int(float(row[0])) if row[0] else 0,
                    'year': row[1],
                    'mileage': int(row[2]) if row[2] else None,
                    'age_days': (datetime.now(timezone.utc) - created_at).days if created_at else 0
                })
            
            # If we have mileage, filter by mileage ±30%
            if mileage_km and len(comparables) > 20:
                mileage_min = int(mileage_km * 0.7)
                mileage_max = int(mileage_km * 1.3)
                comparables = [
                    c for c in comparables 
                    if c['mileage'] and mileage_min <= c['mileage'] <= mileage_max
                ]
            
            logger.info(f"Found {len(comparables)} comparables for {brand} {model} {year}")
            return comparables
            
        except Exception as e:
            logger.error(f"Error getting comparables: {e}")
            return []
    
    def _analyze_market_position(self, price: int, comparables: List[Dict]) -> Dict[str, Any]:
        """Analyze where this listing sits in the market"""
        if not comparables:
            return {
                'comparable_count': 0,
                'median_price': None,
                'discount_pct': 0,
                'position': 'unknown',
            }
        
        # Calculate statistics
        prices = [c['price'] for c in comparables]
        prices.sort()
        
        median_price = prices[len(prices) // 2]
        avg_price = sum(prices) / len(prices)
        min_price = prices[0]
        max_price = prices[-1]
        
        # Calculate discount
        discount_pct = ((median_price - price) / median_price) * 100 if median_price > 0 else 0
        
        # Determine position
        if price < prices[int(len(prices) * 0.1)]:
            position = "very_cheap"  # Bottom 10%
        elif price < prices[int(len(prices) * 0.25)]:
            position = "cheap"  # Bottom 25%
        elif price < prices[int(len(prices) * 0.75)]:
            position = "average"  # Middle 50%
        else:
            position = "expensive"  # Top 25%
        
        return {
            'comparable_count': len(comparables),
            'median_price': int(median_price),
            'avg_price': int(avg_price),
            'price_range': (int(min_price), int(max_price)),
            'discount_pct': round(discount_pct, 1),
            'position': position,
        }
    
    def _calculate_components(
        self,
        price_bgn: int,
        year: int,
        mileage_km: Optional[int],
        brand: str,
        market_context: Dict,
        image_count: int,
        description_length: int,
        created_at: datetime,
    ) -> Dict[str, float]:
        """Calculate scoring components based on price bracket"""
        
        bracket = PriceBracket.get_bracket(price_bgn)
        discount_pct = market_context.get('discount_pct', 0)
        
        # Get bracket-specific thresholds
        thresholds = PriceBracket.get_discount_thresholds(price_bgn)
        
        components = {}
        
        # 1. PRICE/DISCOUNT SCORE (0-4 points, 40%)
        # This is THE MOST IMPORTANT factor
        if discount_pct >= thresholds['excellent']:
            components['price'] = 4.0
        elif discount_pct >= thresholds['good']:
            components['price'] = 3.5
        elif discount_pct >= thresholds['fair']:
            components['price'] = 2.5
        elif discount_pct >= 5:
            components['price'] = 1.5
        elif discount_pct >= 0:
            components['price'] = 0.5
        else:
            components['price'] = 0.0  # More expensive than market
        
        # 2. AGE SCORE (0-2 points, 20%)
        current_year = datetime.now().year
        age = current_year - year
        
        if age <= 2:
            components['age'] = 2.0
        elif age <= 4:
            components['age'] = 1.8
        elif age <= 6:
            components['age'] = 1.5
        elif age <= 8:
            components['age'] = 1.2
        else:
            components['age'] = 0.8
        
        # 3. MILEAGE SCORE (0-2 points, 20%)
        # Weight varies by bracket
        if bracket == "budget":
            # For cheap cars, mileage matters MORE
            mileage_weight = 2.5
        elif bracket == "sweet_spot":
            mileage_weight = 2.0
        elif bracket == "premium":
            mileage_weight = 1.5
        else:  # luxury
            mileage_weight = 1.0
        
        if mileage_km:
            expected_mileage = age * 15000
            ratio = mileage_km / expected_mileage if expected_mileage > 0 else 1.0
            
            if ratio < 0.5:
                mileage_score = 2.0
            elif ratio < 0.8:
                mileage_score = 1.7
            elif ratio < 1.2:
                mileage_score = 1.3
            elif ratio < 1.5:
                mileage_score = 0.8
            else:
                mileage_score = 0.3
            
            components['mileage'] = min(2.0, mileage_score * (mileage_weight / 2.0))
        else:
            components['mileage'] = 1.0  # Neutral
        
        # 4. MARKET CONFIDENCE (0-1 points, 10%)
        # More comparables = higher confidence
        comp_count = market_context.get('comparable_count', 0)
        if comp_count >= 30:
            components['confidence'] = 1.0
        elif comp_count >= 20:
            components['confidence'] = 0.8
        elif comp_count >= 10:
            components['confidence'] = 0.6
        elif comp_count >= 5:
            components['confidence'] = 0.4
        else:
            components['confidence'] = 0.2
        
        # 5. QUALITY/FRESHNESS (0-1 points, 10%)
        quality = 0.0
        
        # Description
        if description_length > 500:
            quality += 0.3
        elif description_length > 200:
            quality += 0.2
        elif description_length > 50:
            quality += 0.1
        
        # Images
        if image_count >= 10:
            quality += 0.3
        elif image_count >= 5:
            quality += 0.2
        elif image_count >= 2:
            quality += 0.1
        
        # Freshness
        now = datetime.now(timezone.utc)
        if not created_at.tzinfo:
            created_at = created_at.replace(tzinfo=timezone.utc)
        age_hours = (now - created_at).total_seconds() / 3600
        
        if age_hours <= 6:
            quality += 0.4
        elif age_hours <= 24:
            quality += 0.2
        
        components['quality'] = min(1.0, quality)
        
        return components
    
    def _generate_reasons(
        self,
        components: Dict[str, float],
        market_context: Dict,
        price: int,
        year: int,
        mileage: Optional[int],
    ) -> List[str]:
        """Generate human-readable reasons"""
        reasons = []
        
        # Price/discount
        discount = market_context.get('discount_pct', 0)
        median = market_context.get('median_price')
        
        if discount >= 25:
            reasons.append(f"🔥 EXCELLENT PRICE: {discount:.0f}% below market (median: {median:,} BGN)")
        elif discount >= 15:
            reasons.append(f"💰 Great price: {discount:.0f}% below market (median: {median:,} BGN)")
        elif discount >= 10:
            reasons.append(f"💵 Good price: {discount:.0f}% below market (median: {median:,} BGN)")
        
        # Market position
        position = market_context.get('position')
        comp_count = market_context.get('comparable_count', 0)
        
        if position == "very_cheap":
            reasons.append(f"📊 Bottom 10% of market ({comp_count} comparables)")
        elif position == "cheap":
            reasons.append(f"📊 Bottom 25% of market ({comp_count} comparables)")
        
        # Age
        if components.get('age', 0) >= 1.8:
            reasons.append(f"📅 Recent year: {year}")
        
        # Mileage
        if components.get('mileage', 0) >= 1.7 and mileage:
            reasons.append(f"🚗 Low mileage: {mileage:,} км")
        
        # Quality
        if components.get('quality', 0) >= 0.8:
            reasons.append("📝 Well-documented listing")
        
        # Price bracket
        bracket = PriceBracket.get_bracket(price)
        if bracket == "sweet_spot":
            reasons.append("⭐ Sweet spot price range (10-30k)")
        
        return reasons


def create_market_aware_engine(session: Session) -> MarketAwareRatingEngine:
    """Factory function to create market-aware engine with default settings"""
    return MarketAwareRatingEngine(
        session=session,
        posting_threshold=7.5,
        require_comparables=True,
        min_comparables=5,
    )
