"""
Telegram webhook router
"""
from fastapi import APIRouter, Header, HTTPException, Request

from configs.settings import settings

router = APIRouter()


@router.post("/webhook")
async def telegram_webhook(request: Request, x_telegram_bot_api_secret_token: str = Header(None)):
    """
    Telegram webhook endpoint for bot updates
    """
    # Verify webhook secret
    if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")
    
    # TODO: Process Telegram update with aiogram
    update_data = await request.json()
    
    return {"ok": True}
