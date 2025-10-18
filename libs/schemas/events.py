"""
Event payload schemas
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ListingEvent(BaseModel):
    """Canonical event payload for pipeline tasks"""
    
    listing_id: UUID
    source_id: str
    site_ad_id: str
    url: str
    listing_version: int = 1
    
    # Hashes
    description_hash: Optional[str] = None
    first_image_hash: Optional[str] = None
    
    # Timestamps
    first_seen_at: datetime
    last_seen_at: datetime
    
    # Normalized fields snapshot
    brand_id: Optional[str] = None
    model_id: Optional[str] = None
    year: Optional[int] = None
    mileage_km: Optional[int] = None
    fuel: Optional[str] = None
    gearbox: Optional[str] = None
    body: Optional[str] = None
    price_bgn: Optional[float] = None
    region: Optional[str] = None
    
    # State flags
    is_active: bool = True
    is_duplicate: bool = False
    duplicate_of: Optional[UUID] = None
    
    # Provenance timestamps
    parsed_at: Optional[datetime] = None
    normalized_at: Optional[datetime] = None
    priced_at: Optional[datetime] = None
    ai_eval_at: Optional[datetime] = None
    scored_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
