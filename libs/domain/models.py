"""
Database models for CarScout AI
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey, 
    Integer, JSON, Numeric, String, Text, BigInteger, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Source(Base):
    """Marketplace sources (Mobile.bg, Cars.bg, etc.)"""
    __tablename__ = "sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False, unique=True)
    base_url = Column(String(255), nullable=False)
    robots_cache = Column(JSON)
    enabled = Column(Boolean, default=True)
    crawl_interval_s = Column(Integer, default=120)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ListingRaw(Base):
    """Raw scraped listings"""
    __tablename__ = "listings_raw"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    site_ad_id = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    raw_html_path = Column(String(500))  # S3 path
    raw_html = Column(Text)  # Temporary storage before S3 upload
    parsed_data = Column(JSON)  # Spider-extracted structured data
    first_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    http_status = Column(Integer)
    etag = Column(String(100))
    last_modified = Column(String(100))
    parse_errors = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    source = relationship("Source")
    normalized = relationship("ListingNormalized", back_populates="raw", uselist=False)
    
    __table_args__ = (
        Index("idx_source_site_ad", "source_id", "site_ad_id", unique=True),
        Index("idx_is_active", "is_active"),
        Index("idx_first_seen", "first_seen_at"),
    )


class BrandModel(Base):
    """Brand and model mappings with aliases"""
    __tablename__ = "brand_models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    brand = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    aliases = Column(JSON, default=list)  # Alternative spellings
    locale = Column(String(10), default="bg")
    normalized_brand = Column(String(100), nullable=False)
    normalized_model = Column(String(100), nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_brand_model", "normalized_brand", "normalized_model"),
    )


class ListingNormalized(Base):
    """Normalized and processed listings"""
    __tablename__ = "listings_normalized"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    raw_id = Column(UUID(as_uuid=True), ForeignKey("listings_raw.id"), nullable=False)
    brand_id = Column(String(100))
    model_id = Column(String(100))
    year = Column(Integer)
    mileage_km = Column(Integer)
    fuel = Column(String(50))
    gearbox = Column(String(50))
    body = Column(String(50))
    price_bgn = Column(Numeric(10, 2))
    currency = Column(String(10))
    region = Column(String(100))
    title = Column(Text)
    description = Column(Text)
    features = Column(JSON)
    description_hash = Column(String(64))
    first_image_hash = Column(String(64))
    listing_version = Column(Integer, default=1)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of = Column(UUID(as_uuid=True), ForeignKey("listings_normalized.id"))
    seller_id = Column(UUID(as_uuid=True), ForeignKey("sellers.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    raw = relationship("ListingRaw", back_populates="normalized")
    seller = relationship("Seller")
    images = relationship("Image", back_populates="listing")
    comp_cache = relationship("CompCache", back_populates="listing", uselist=False)
    evaluation = relationship("Evaluation", back_populates="listing", uselist=False)
    score = relationship("Score", back_populates="listing", uselist=False)
    
    __table_args__ = (
        Index("idx_brand_model_year", "brand_id", "model_id", "year"),
        Index("idx_price", "price_bgn"),
        Index("idx_is_duplicate", "is_duplicate"),
        Index("idx_description_hash", "description_hash"),
    )


class Image(Base):
    """Listing images"""
    __tablename__ = "images"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings_normalized.id"), nullable=False)
    url = Column(String(500), nullable=False)
    object_key = Column(String(500))  # S3 key
    hash = Column(String(64))  # Image hash for deduplication
    width = Column(Integer)
    height = Column(Integer)
    index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    listing = relationship("ListingNormalized", back_populates="images")


class Seller(Base):
    """Sellers (identified by phone hash)"""
    __tablename__ = "sellers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    phone_hash = Column(String(64), unique=True, nullable=False)
    name = Column(String(200))
    site_profile_url = Column(String(500))
    contact_count = Column(Integer, default=0)
    blacklist = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_blacklist", "blacklist", postgresql_where="blacklist = true"),
    )


class PriceHistory(Base):
    """Price history for listings"""
    __tablename__ = "prices_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings_normalized.id"), nullable=False)
    price_bgn = Column(Numeric(10, 2), nullable=False)
    seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_listing_seen", "listing_id", "seen_at"),
    )


class CompCache(Base):
    """Cached comparable prices"""
    __tablename__ = "comps_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings_normalized.id"), nullable=False)
    predicted_price_bgn = Column(Numeric(10, 2))
    discount_pct = Column(Float)
    sample_size = Column(Integer)
    p50 = Column(Numeric(10, 2))
    p10 = Column(Numeric(10, 2))
    p90 = Column(Numeric(10, 2))
    features = Column(JSON)
    computed_at = Column(DateTime, default=datetime.utcnow)
    model_version = Column(String(50))
    
    listing = relationship("ListingNormalized", back_populates="comp_cache")


class Evaluation(Base):
    """AI risk evaluations"""
    __tablename__ = "evaluations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings_normalized.id"), nullable=False)
    flags = Column(JSON)
    risk_level = Column(Enum("low", "medium", "high", name="risk_level_enum"))
    llm_summary = Column(Text)
    llm_confidence = Column(Float)
    rule_confidence = Column(Float)
    model_versions = Column(JSON)
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    
    listing = relationship("ListingNormalized", back_populates="evaluation")


class Score(Base):
    """Final listing scores"""
    __tablename__ = "scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings_normalized.id"), nullable=False)
    score = Column(Float, nullable=False)
    reasons = Column(JSON)
    freshness_bonus = Column(Float)
    liquidity = Column(Float)
    risk_penalty = Column(Float)
    final_state = Column(Enum("draft", "approved", "rejected", name="final_state_enum"))
    scored_at = Column(DateTime, default=datetime.utcnow)
    
    listing = relationship("ListingNormalized", back_populates="score")
    
    __table_args__ = (
        Index("idx_score_state", "score", "final_state"),
    )


class User(Base):
    """Application users"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    telegram_user_id = Column(BigInteger, unique=True)
    email = Column(String(255), unique=True)
    role = Column(Enum("user", "admin", name="user_role_enum"), default="user")
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    alerts = relationship("Alert", back_populates="user")


class Plan(Base):
    """Subscription plans"""
    __tablename__ = "plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(Enum("Free", "Premium", "Pro", name="plan_name_enum"), nullable=False, unique=True)
    limits = Column(JSON)  # {max_alerts: 3, delay_minutes: 30}
    price_bgn = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)


class Subscription(Base):
    """User subscriptions"""
    __tablename__ = "subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    status = Column(Enum("active", "past_due", "canceled", name="subscription_status_enum"))
    billing_provider = Column(Enum("Stripe", "Telegram", name="billing_provider_enum"))
    provider_customer_id = Column(String(100))
    provider_sub_id = Column(String(100))
    current_period_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="subscription")
    plan = relationship("Plan")


class Alert(Base):
    """User price alerts"""
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    dsl_query = Column(Text, nullable=False)
    normalized_filters = Column(JSON, nullable=False)
    plan_required = Column(String(50))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="alerts")
    matches = relationship("AlertMatch", back_populates="alert")


class AlertMatch(Base):
    """Matched listings for alerts"""
    __tablename__ = "alert_matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id"), nullable=False)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings_normalized.id"), nullable=False)
    matched_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime)
    delivery_status = Column(Enum("pending", "delivered", "skipped", "failed", name="delivery_status_enum"))
    reason = Column(Text)
    
    alert = relationship("Alert", back_populates="matches")


class ChannelPost(Base):
    """Posted listings to Telegram channel"""
    __tablename__ = "channel_posts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings_normalized.id"), nullable=False)
    telegram_message_id = Column(BigInteger, nullable=False)
    posted_at = Column(DateTime, default=datetime.utcnow)
    channel = Column(String(100))
    status = Column(String(50))
    
    __table_args__ = (
        Index("idx_listing_channel", "listing_id", "channel", unique=True),
    )


class DedupeSignature(Base):
    """Deduplication signatures"""
    __tablename__ = "dedupe_signatures"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings_normalized.id"), nullable=False, unique=True)
    title_trgm = Column(Text)  # For pg_trgm
    title_minhash = Column(String(256))
    desc_minhash = Column(String(256))
    first_image_phash = Column(BigInteger)
    # embeddings column requires pgvector - added in migration
    created_at = Column(DateTime, default=datetime.utcnow)


class DuplicateLog(Base):
    """Log of duplicate detections"""
    __tablename__ = "duplicates_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings_normalized.id"), nullable=False)
    duplicate_of = Column(UUID(as_uuid=True), ForeignKey("listings_normalized.id"), nullable=False)
    method = Column(Enum("heuristic", "embedding", "image", name="dedupe_method_enum"))
    score = Column(Float)
    decided_at = Column(DateTime, default=datetime.utcnow)
