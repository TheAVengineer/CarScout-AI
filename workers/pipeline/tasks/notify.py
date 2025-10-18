"""
Notification task - Post to channel and send user alerts
"""
from uuid import UUID
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton

from workers.pipeline.celery_app import celery_app
from libs.domain.database import get_sync_session
from libs.domain.models import ListingNormalized, Score, ChannelPost, Image, AlertMatch, User
from libs.domain.alert_matcher import AlertMatcher
from configs.settings import settings


@celery_app.task(bind=True, max_retries=3)
def match_alerts(self, listing_id: str):
    """
    Match listing against user alerts and queue notifications
    
    Args:
        listing_id: UUID of the listing
    """
    session = get_sync_session()
    
    try:
        # Get listing
        listing = session.query(ListingNormalized).filter_by(id=UUID(listing_id)).first()
        if not listing:
            return {"status": "error", "message": "Listing not found"}
        
        # Initialize alert matcher
        matcher = AlertMatcher(session)
        
        # Find matching alerts
        matching_alerts = matcher.find_matching_alerts(listing)
        
        matched_count = 0
        queued_count = 0
        
        for alert in matching_alerts:
            # Create alert match record
            alert_match = AlertMatch(
                alert_id=alert.id,
                listing_id=listing.id,
                matched_at=datetime.now(timezone.utc),
                notified=False,
            )
            session.add(alert_match)
            session.commit()
            matched_count += 1
            
            # Check if user should be notified
            if matcher.should_notify_user(alert.user, alert, listing):
                # Queue notification
                send_user_alert.delay(listing_id, str(alert.user_id), str(alert.id))
                queued_count += 1
        
        session.commit()
        
        return {
            "status": "matched",
            "listing_id": listing_id,
            "matched_count": matched_count,
            "queued_count": queued_count,
        }
        
    except Exception as e:
        session.rollback()
        raise self.retry(exc=e, countdown=60)
    finally:
        session.close()


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
        
        # Match alerts and send notifications
        match_alerts.delay(listing_id)
        
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
        
        # Get user
        user = session.query(User).filter_by(id=UUID(user_id)).first()
        if not user:
            return {"status": "error", "message": "User not found"}
        
        # Get alert match
        alert_match = session.query(AlertMatch).filter_by(
            listing_id=UUID(listing_id),
            alert_id=UUID(alert_id),
        ).first()
        
        if not alert_match:
            return {"status": "error", "message": "Alert match not found"}
        
        # Format message
        message = _format_alert_message(listing, user.plan.name if user.plan else "Free")
        
        # Get user telegram ID
        telegram_user_id = user.telegram_id
        
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
        # Mark alert match as notified
        alert_match.notified = True
        alert_match.notified_at = datetime.now(timezone.utc)
        session.commit()
        
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


def _format_alert_message(listing: ListingNormalized, plan_name: str = "Free") -> str:
    """Format message for personal alerts"""
    
    # Discount info
    discount_info = ""
    if listing.discount_pct and listing.discount_pct > 5:
        discount_info = f"\n💵 Отстъпка: <b>{listing.discount_pct:.1f}%</b> под пазарната цена"
    
    message = f"""
🔔 <b>Нова обява отговаря на твоята бдителност!</b>

<b>{listing.title}</b>

💰 Цена: <b>{listing.price_bgn:.0f} лв</b>{discount_info}
📅 Година: {listing.year}
⛽ {listing.fuel or 'N/A'} | 📏 {listing.mileage_km:,} км
⚙️ {listing.gearbox or 'N/A'}

📍 {listing.region or 'N/A'}
"""
    
    return message.strip()
