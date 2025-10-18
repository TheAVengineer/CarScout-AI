"""
Admin router for internal operations
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class RescrapeRequest(BaseModel):
    source_id: str
    url: str | None = None
    count: int = 100


class ReEvaluateRequest(BaseModel):
    listing_ids: list[str]


class BlacklistSellerRequest(BaseModel):
    phone_hash: str | None = None
    seller_id: str | None = None


@router.post("/rescrape")
async def rescrape(request: RescrapeRequest):
    """Trigger a rescrape for a specific source"""
    # TODO: Enqueue scraping tasks
    return {"status": "queued", "source_id": request.source_id}


@router.post("/re-evaluate")
async def re_evaluate(request: ReEvaluateRequest):
    """Re-evaluate listings through the AI pipeline"""
    # TODO: Enqueue re-evaluation tasks
    return {"status": "queued", "count": len(request.listing_ids)}


@router.post("/blacklist/seller")
async def blacklist_seller(request: BlacklistSellerRequest):
    """Blacklist a seller by phone hash or seller ID"""
    # TODO: Update seller blacklist status
    return {"status": "blacklisted"}


@router.get("/brand-models")
async def get_brand_models():
    """Get all brand-model mappings"""
    # TODO: Fetch from database
    return {"brand_models": []}


@router.post("/brand-models")
async def create_brand_model():
    """Create or update brand-model mapping"""
    # TODO: Create/update in database
    return {"status": "created"}
