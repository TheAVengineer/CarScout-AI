"""
Public API router for external access
"""
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/listings/{listing_id}")
async def get_listing(listing_id: str):
    """Get details of a specific listing"""
    # TODO: Fetch from database
    return {"listing_id": listing_id, "details": {}}


@router.post("/users/link-telegram")
async def link_telegram():
    """Link a Telegram account to user profile"""
    # TODO: Implement Telegram linking flow
    return {"status": "linked"}
