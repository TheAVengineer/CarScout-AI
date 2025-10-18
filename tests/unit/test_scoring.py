"""
Basic unit tests for scoring engine
"""
import pytest
from libs.domain.scoring import ScoringEngine


def test_calculate_score_high_discount():
    """Test scoring with high discount percentage"""
    engine = ScoringEngine()
    result = engine.calculate_score(
        discount_pct=20.0,
        comp_sample_size=50,
        comp_confidence=0.8,
        risk_level="low",
        freshness_hours=1.0,
    )
    
    assert result["score"] >= 8.0
    assert result["is_approved"] is True
    assert result["price_score"] > 3.0


def test_calculate_score_high_risk():
    """Test scoring with high risk level"""
    engine = ScoringEngine()
    result = engine.calculate_score(
        discount_pct=15.0,
        comp_sample_size=50,
        comp_confidence=0.8,
        risk_level="high",
        freshness_hours=1.0,
    )
    
    assert result["risk_penalty"] < -3.0
    assert result["score"] < 7.5


def test_calculate_score_insufficient_comps():
    """Test scoring with insufficient comparable listings"""
    engine = ScoringEngine()
    result = engine.calculate_score(
        discount_pct=15.0,
        comp_sample_size=10,
        comp_confidence=0.8,
        risk_level="low",
        freshness_hours=1.0,
    )
    
    assert result["is_approved"] is False


def test_freshness_bonus():
    """Test freshness bonus calculation"""
    engine = ScoringEngine()
    
    # Very fresh (< 1 hour)
    result1 = engine.calculate_score(
        discount_pct=10.0,
        comp_sample_size=50,
        comp_confidence=0.8,
        risk_level="low",
        freshness_hours=0.5,
    )
    
    # Old (> 24 hours)
    result2 = engine.calculate_score(
        discount_pct=10.0,
        comp_sample_size=50,
        comp_confidence=0.8,
        risk_level="low",
        freshness_hours=48.0,
    )
    
    assert result1["freshness_bonus"] > result2["freshness_bonus"]
