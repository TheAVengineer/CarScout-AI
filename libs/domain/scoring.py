"""
Scoring domain logic
"""
from typing import Dict, Any


class ScoringEngine:
    """Calculate listing scores based on various factors"""
    
    def __init__(
        self,
        approval_threshold: float = 7.5,
        min_sample_size: int = 30,
        min_confidence: float = 0.6,
    ):
        self.approval_threshold = approval_threshold
        self.min_sample_size = min_sample_size
        self.min_confidence = min_confidence
    
    def calculate_score(
        self,
        discount_pct: float,
        comp_sample_size: int,
        comp_confidence: float,
        risk_level: str,
        freshness_hours: float,
    ) -> Dict[str, Any]:
        """
        Calculate final score for a listing
        
        Args:
            discount_pct: Percentage discount from market price
            comp_sample_size: Number of comparable listings
            comp_confidence: Confidence in price estimate
            risk_level: Risk classification (low, medium, high)
            freshness_hours: Hours since first seen
            
        Returns:
            Dictionary with score, components, and approval status
        """
        # Price advantage (0-5 points)
        price_score = self._calculate_price_score(discount_pct, comp_confidence)
        
        # Risk penalty (0 to -4 points)
        risk_penalty = self._calculate_risk_penalty(risk_level)
        
        # Freshness bonus (0-0.5 points)
        freshness_bonus = self._calculate_freshness_bonus(freshness_hours)
        
        # Liquidity bonus (0-1 points) - placeholder
        liquidity_bonus = 0.5 if comp_sample_size >= self.min_sample_size else 0.0
        
        # Calculate total
        total_score = max(1.0, min(10.0, price_score + risk_penalty + freshness_bonus + liquidity_bonus))
        
        # Determine approval
        is_approved = (
            total_score >= self.approval_threshold
            and comp_sample_size >= self.min_sample_size
            and comp_confidence >= self.min_confidence
        )
        
        return {
            "score": round(total_score, 2),
            "price_score": price_score,
            "risk_penalty": risk_penalty,
            "freshness_bonus": freshness_bonus,
            "liquidity_bonus": liquidity_bonus,
            "is_approved": is_approved,
            "reasons": self._generate_reasons(
                discount_pct, risk_level, comp_sample_size, comp_confidence
            ),
        }
    
    def _calculate_price_score(self, discount_pct: float, confidence: float) -> float:
        """Calculate score based on price advantage"""
        if discount_pct >= 20:
            base_score = 5.0
        elif discount_pct >= 15:
            base_score = 4.0
        elif discount_pct >= 10:
            base_score = 3.0
        elif discount_pct >= 5:
            base_score = 2.0
        else:
            base_score = 1.0
        
        # Adjust for confidence
        return base_score * confidence
    
    def _calculate_risk_penalty(self, risk_level: str) -> float:
        """Calculate penalty based on risk classification"""
        risk_penalties = {
            "low": 0.0,
            "medium": -1.5,
            "high": -3.5,
        }
        return risk_penalties.get(risk_level, -2.0)
    
    def _calculate_freshness_bonus(self, hours: float) -> float:
        """Calculate bonus for fresh listings"""
        if hours <= 1:
            return 0.5
        elif hours <= 6:
            return 0.3
        elif hours <= 24:
            return 0.1
        return 0.0
    
    def _generate_reasons(
        self,
        discount_pct: float,
        risk_level: str,
        sample_size: int,
        confidence: float,
    ) -> list[str]:
        """Generate human-readable reasons for the score"""
        reasons = []
        
        if discount_pct >= 15:
            reasons.append(f"Excellent price ({discount_pct:.1f}% below market)")
        elif discount_pct >= 10:
            reasons.append(f"Good price ({discount_pct:.1f}% below market)")
        
        if risk_level == "low":
            reasons.append("Low risk indicators")
        elif risk_level == "high":
            reasons.append("⚠️ High risk indicators detected")
        
        if sample_size < 20:
            reasons.append(f"Limited comparables ({sample_size} similar listings)")
        
        if confidence < 0.7:
            reasons.append("Price estimate has moderate uncertainty")
        
        return reasons
