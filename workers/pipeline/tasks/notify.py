"""
Notification task - Post to channel and send user alerts
"""
from uuid import UUID
from datetime import datetime

from aiogram import Bot
from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton

from workers.pipeline.celery_app import celery_app
from libs.domain.database import get_sync_session
from libs.domain.models import ListingNormalized, Score, ChannelPost, Image
from configs.settings import settings


@celery_app.task(bind=True, max_retries=3, rate_limit="20/h")
def post_to_channel(self, listing_id: str):
    """
    Post approved listing to Telegram channel
    
    Args:
        listing_id: UUID of the listing
    """
    session = get_sync_session()
    
    try:
        # Get listing and score
        listing = session.query(ListingNormalized).filter_by(id=UUID(listing_id)).first()
        if not listing:
            return {"status": "error", "message": "Listing not found"}
        
        score = session.query(Score).filter_by(listing_id=listing.id).first()
        if not score or score.final_state != "approved":
            return {"status": "skipped", "message": "Not approved"}
        
        # Check if already posted
        existing_post = session.query(ChannelPost).filter_by(
            listing_id=listing.id,
            channel=settings.TELEGRAM_CHANNEL_ID
        ).first()
        
        if existing_post:
            return {"status": "skipped", "message": "Already posted"}
        
        # Format message
        message = _format_channel_message(listing, score)
        
        # Get images
        images = session.query(Image).filter_by(listing_id=listing.id).order_by(Image.index).limit(5).all()
        
        # Create inline keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Виж обява", url=listing.raw.url)],
            [
                InlineKeyboardButton(text="💾 Запази", callback_data=f"save_{listing.id}"),
                InlineKeyboardButton(text="📞 Резервирай", callback_data=f"reserve_{listing.id}"),
            ],
        ])
        
        # Post to Telegram
        bot = Bot(token=settings.TELEGRAM_CHANNEL_BOT_TOKEN)
        
        if images and len(images) > 1:
            # Post as media group
            media = [
                InputMediaPhoto(media=img.url, caption=message if i == 0 else "")
                for i, img in enumerate(images)
            ]
            messages = bot.send_media_group(chat_id=settings.TELEGRAM_CHANNEL_ID, media=media)
            message_id = messages[0].message_id if messages else 0
            
            # Send keyboard separately
            if message_id:
                bot.send_message(
                    chat_id=settings.TELEGRAM_CHANNEL_ID,
                    text="👆 Опции за тази обява:",
                    reply_markup=keyboard,
                )
        else:
            # Post single photo
            photo_url = images[0].url if images else None
            if photo_url:
                result = bot.send_photo(
                    chat_id=settings.TELEGRAM_CHANNEL_ID,
                    photo=photo_url,
                    caption=message,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
                message_id = result.message_id
            else:
                result = bot.send_message(
                    chat_id=settings.TELEGRAM_CHANNEL_ID,
                    text=message,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
                message_id = result.message_id
        
        # Save channel post
        channel_post = ChannelPost(
            listing_id=listing.id,
            telegram_message_id=message_id,
            channel=settings.TELEGRAM_CHANNEL_ID,
            status="posted",
        )
        session.add(channel_post)
        session.commit()
        
        return {
            "status": "posted",
            "listing_id": listing_id,
            "message_id": message_id,
        }
        
    except Exception as e:
        session.rollback()
        self.logger.error(f"Error posting to channel: {e}")
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes
    finally:
        session.close()


@celery_app.task(bind=True, max_retries=3)
def send_user_alert(self, listing_id: str, user_id: str, alert_id: str):
    """
    Send personal alert to user
    
    Args:
        listing_id: UUID of the listing
        user_id: UUID of the user
        alert_id: UUID of the alert
    """
    session = get_sync_session()
    
    try:
        # Get listing
        listing = session.query(ListingNormalized).filter_by(id=UUID(listing_id)).first()
        if not listing:
            return {"status": "error", "message": "Listing not found"}
        
        # TODO: Get user and check plan limits
        # TODO: Apply plan-based delay
        # TODO: Check daily caps
        
        # Format message
        message = _format_alert_message(listing)
        
        # Get user telegram ID
        # user = session.query(User).filter_by(id=UUID(user_id)).first()
        # telegram_user_id = user.telegram_user_id
        
        # For now, send to a test user
        telegram_user_id = 123456789  # TODO: Get from database
        
        # Send via Telegram Bot
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Виж обява", url=listing.raw.url)],
        ])
        
        result = bot.send_message(
            chat_id=telegram_user_id,
            text=message,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        
        # Log notification
        # TODO: Update alert_matches table
        
        return {
            "status": "sent",
            "listing_id": listing_id,
            "user_id": user_id,
            "message_id": result.message_id,
        }
        
    except Exception as e:
        session.rollback()
        self.logger.error(f"Error sending user alert: {e}")
        raise self.retry(exc=e, countdown=60)
    finally:
        session.close()


def _format_channel_message(listing: ListingNormalized, score: Score) -> str:
    """Format message for channel posting"""
    # Score emoji
    score_value = score.score
    if score_value >= 9:
        score_emoji = "🔥🔥🔥"
    elif score_value >= 8:
        score_emoji = "🔥🔥"
    elif score_value >= 7:
        score_emoji = "🔥"
    else:
        score_emoji = "⭐"
    
    # Build message
    message = f"""
{score_emoji} <b>{listing.title}</b>

📊 <b>Оценка: {score_value:.1f}/10</b>

💰 Цена: <b>{listing.price_bgn:.0f} лв</b>
📅 Година: {listing.year}
⛽ Гориво: {listing.fuel or 'N/A'}
📏 Пробег: {listing.mileage_km:,} км
⚙️ Скоростна кутия: {listing.gearbox or 'N/A'}

📍 Регион: {listing.region or 'N/A'}

<b>Защо си струва:</b>
"""
    
    # Add reasons
    reasons = score.reasons or []
    for reason in reasons[:3]:  # Top 3 reasons
        message += f"• {reason}\n"
    
    return message.strip()


def _format_alert_message(listing: ListingNormalized) -> str:
    """Format message for personal alerts"""
    message = f"""
🔔 <b>Нова обява отговаря на твоята бдителност!</b>

<b>{listing.title}</b>

💰 Цена: <b>{listing.price_bgn:.0f} лв</b>
📅 Година: {listing.year}
⛽ {listing.fuel or 'N/A'} | 📏 {listing.mileage_km:,} км
⚙️ {listing.gearbox or 'N/A'}

📍 {listing.region or 'N/A'}
"""
    
    return message.strip()
