"""
Database-Based Deal Monitor

Instead of scraping, this monitor:
1. Queries database for recently added/updated listings (last 5 min)
2. Scores them using comparable vehicles
3. Posts good deals to Telegram

This avoids the complex Playwright yielding issues in the spider approach.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy import create_engine, select, and_, or_, func, cast, Integer, String
from sqlalchemy.orm import sessionmaker
from celery import shared_task

from libs.domain.models import ListingRaw
from configs.settings import settings

logger = logging.getLogger(__name__)


@shared_task(name="monitor_database_deals", soft_time_limit=600, time_limit=700)
def monitor_database_deals():
    """
    Monitor database for new/updated listings and post high-score deals to Telegram.
    
    This runs every 5 minutes and processes listings added/updated
    in the last 5 minutes (matching run frequency to reduce clustering).
    """
    logger.info("🔍 Starting database deal monitor...")
    
    try:
        # Create database session
        engine = create_engine(settings.DATABASE_SYNC_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Get listings from last 5 minutes (matches run frequency)
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        
        # Query both NEW listings and UPDATED listings (price drops can be good deals!)
        # But only show listings that are relatively fresh (added in last 7 days)
        fresh_listing_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        
        query = session.query(ListingRaw).filter(
            and_(
                or_(
                    ListingRaw.first_seen_at >= cutoff_time,  # New listings
                    ListingRaw.updated_at >= cutoff_time      # Updated listings (price drops!)
                ),
                ListingRaw.first_seen_at >= fresh_listing_cutoff,  # Only listings from last 7 days
                ListingRaw.is_active == True,
                ListingRaw.parsed_data.isnot(None)
            )
        ).order_by(ListingRaw.first_seen_at.desc())
        
        listings = query.all()
        logger.info(f"📊 Found {len(listings)} new/updated listings to evaluate (max 7 days old)")
        
        if not listings:
            logger.info("✅ No new listings to process")
            session.close()
            return {'status': 'success', 'processed': 0}
        
        # Process each listing
        processed = 0
        high_scores = 0
        posted_count = 0  # Track how many deals posted to Telegram
        MAX_POSTS_PER_RUN = 3  # Rate limit to reduce clustering
        score_distribution = {'3.0': 0, '4-5': 0, '6-7': 0, '7.5+': 0}
        
        for listing in listings:
            try:
                # Extract fields from parsed_data JSON
                data = listing.parsed_data
                brand = data.get('brand')
                model = data.get('model')
                year = data.get('year')
                price = data.get('price')
                
                if not all([brand, model, year, price]):
                    logger.debug(f"⏭️  Skipping {listing.site_ad_id} - missing required fields")
                    continue
                
                # Try to convert year to int
                try:
                    year = int(year) if isinstance(year, str) else year
                except (ValueError, TypeError):
                    logger.debug(f"⏭️  Skipping {listing.site_ad_id} - invalid year: {year}")
                    continue
                
                # Check mileage - skip if too high (>250k km) or missing
                mileage_km = data.get('mileage_km')
                if mileage_km is None:
                    logger.debug(f"⏭️  Skipping {listing.site_ad_id} - missing mileage data")
                    continue
                
                # Convert mileage to int if needed
                try:
                    mileage_km = int(mileage_km) if isinstance(mileage_km, str) else mileage_km
                except (ValueError, TypeError):
                    logger.debug(f"⏭️  Skipping {listing.site_ad_id} - invalid mileage: {mileage_km}")
                    continue
                
                # Filter out high mileage cars (>250k km)
                if mileage_km > 250000:
                    logger.debug(f"⏭️  Skipping {listing.site_ad_id} - mileage too high: {mileage_km:,} km")
                    continue
                
                # Score the listing
                score_result = _evaluate_listing(session, listing.site_ad_id, brand, model, year, price)
                
                if isinstance(score_result, dict):
                    score = score_result.get('score')
                    avg_price = score_result.get('avg_price')
                    comp_count = score_result.get('comp_count')
                else:
                    score = score_result
                    avg_price = None
                    comp_count = 0
                
                if score:
                    # Track score distribution
                    if score <= 3.0:
                        score_distribution['3.0'] += 1
                    elif score < 6:
                        score_distribution['4-5'] += 1
                    elif score < 7.5:
                        score_distribution['6-7'] += 1
                    else:
                        score_distribution['7.5+'] += 1
                
                if score and score >= 8.3:
                    high_scores += 1
                    
                    # Rate limit: Only post first 3 high-score deals per run
                    if posted_count < MAX_POSTS_PER_RUN:
                        logger.info(f"🎯 HIGH SCORE: {score:.1f}/10 - {brand} {model} {year} - {price:,.0f} BGN - {mileage_km:,} km - {listing.url}")
                        
                        # Post to Telegram
                        if avg_price and comp_count:
                            if _post_to_telegram(listing, score, avg_price, comp_count):
                                posted_count += 1
                    else:
                        logger.info(f"⏭️ RATE LIMITED: {score:.1f}/10 - {brand} {model} {year} (already posted {posted_count} deals this run)")
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Error processing listing {listing.site_ad_id}: {e}")
                continue
        
        session.close()
        
        logger.info(f"✅ Monitor complete: {processed} processed, {high_scores} high scores, {posted_count}/{MAX_POSTS_PER_RUN} posted to Telegram")
        logger.info(f"📊 Score distribution: {score_distribution['3.0']} insufficient data, "
                   f"{score_distribution['4-5']} fair (4-5), {score_distribution['6-7']} good (6-7), "
                   f"{score_distribution['7.5+']} excellent (7.5+)")
        
        return {
            'status': 'success',
            'processed': processed,
            'high_scores': high_scores,
            'posted_count': posted_count,
            'score_distribution': score_distribution,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Monitor exception: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def _evaluate_listing(session, site_ad_id: str, brand: str, model: str, year: int, price: float) -> Optional[Dict]:
    """
    Score a listing based on market comparison.
    
    Scoring algorithm:
    - Base: 4.0 points
    - Discount ≥25%: +4.0 → 8.0+ (HIGH SCORE)
    - Discount 20-25%: +3.5 → 7.5+ (HIGH SCORE)
    - Discount 15-20%: +2.5 → 6.5
    - Discount 10-15%: +1.5 → 5.5
    - Discount 5-10%: +0.5 → 4.5
    - Premium (negative discount): penalty
    - Recent year (≥2020): +0.3
    
    Returns dict with score, avg_price, comp_count, or None if evaluation failed.
    """
    try:
        # Get comparable vehicles (same brand/model, ±2 years)
        avg_price = _get_comparable_price(session, brand, model, year)
        comp_count = _count_comparables(session, brand, model, year)
        
        if not avg_price or comp_count < 5:
            # Not enough data to compare
            return {
                'score': 3.0,
                'avg_price': avg_price,
                'comp_count': comp_count
            }
        
        # Calculate discount percentage
        discount_pct = ((avg_price - price) / avg_price) * 100
        
        # Base score
        score = 4.0
        
        # Price scoring (most important factor)
        if discount_pct >= 25:
            score += 4.0
        elif discount_pct >= 20:
            score += 3.5
        elif discount_pct >= 15:
            score += 3.0
        elif discount_pct >= 10:
            score += 2.0
        elif discount_pct >= 5:
            score += 1.0
        elif discount_pct >= 0:
            score += 0.5
        else:
            # More expensive than average
            score -= abs(discount_pct) / 10
        
        # Confidence adjustment based on comparable count
        if comp_count >= 20:
            confidence = 1.0
        elif comp_count >= 10:
            confidence = 0.9
        else:
            confidence = 0.8
        
        score = score * confidence
        
        # Feature bonuses
        if year >= 2020:
            score += 0.3
        
        # Clamp to 1-10 range
        score = max(1.0, min(10.0, score))
        
        logger.debug(f"Score {score:.1f}/10 for {brand} {model} {year}: "
                    f"price={price}, avg={avg_price:.0f}, discount={discount_pct:.1f}%, "
                    f"comps={comp_count}")
        
        return {
            'score': score,
            'avg_price': avg_price,
            'comp_count': comp_count,
            'discount_pct': discount_pct
        }
        
    except Exception as e:
        logger.error(f"Error evaluating {brand} {model}: {e}")
        return None


def _get_comparable_price(session, brand: str, model: str, year: int) -> Optional[float]:
    """Get average price of comparable vehicles (same brand/model, ±2 years)
    
    Uses raw SQL to avoid SQLAlchemy JSON field syntax issues.
    """
    try:
        # Use raw SQL for reliability
        sql = """
            SELECT AVG(CAST(parsed_data->>'price' AS INTEGER))
            FROM listings_raw
            WHERE parsed_data->>'brand' = :brand
              AND parsed_data->>'model' = :model
              AND CAST(parsed_data->>'year' AS INTEGER) BETWEEN :year_min AND :year_max
              AND CAST(parsed_data->>'price' AS INTEGER) > 0
              AND is_active = true
        """
        
        from sqlalchemy import text
        result = session.execute(
            text(sql),
            {
                'brand': brand,
                'model': model,
                'year_min': year - 2,
                'year_max': year + 2
            }
        )
        
        avg_price = result.scalar()
        return float(avg_price) if avg_price else None
        
    except Exception as e:
        logger.error(f"Error getting comparable price for {brand} {model}: {e}")
        return None


def _count_comparables(session, brand: str, model: str, year: int) -> int:
    """Count comparable vehicles
    
    Uses raw SQL for reliability.
    """
    try:
        # Use raw SQL for reliability
        sql = """
            SELECT COUNT(*)
            FROM listings_raw
            WHERE parsed_data->>'brand' = :brand
              AND parsed_data->>'model' = :model
              AND CAST(parsed_data->>'year' AS INTEGER) BETWEEN :year_min AND :year_max
              AND CAST(parsed_data->>'price' AS INTEGER) > 0
              AND is_active = true
        """
        
        from sqlalchemy import text
        result = session.execute(
            text(sql),
            {
                'brand': brand,
                'model': model,
                'year_min': year - 2,
                'year_max': year + 2
            }
        )
        
        count = result.scalar()
        return int(count) if count else 0
        
    except Exception as e:
        logger.error(f"Error counting comparables for {brand} {model}: {e}")
        return 0


def _post_to_telegram(listing: ListingRaw, score: float, avg_price: float, comp_count: int):
    """Post high-score listing to Telegram channel
    
    Args:
        listing: The listing to post
        score: The calculated score
        avg_price: Average market price for comparables
        comp_count: Number of comparable vehicles found
    """
    try:
        import requests
        from configs.settings import settings
        
        # Format message with deal details
        data = listing.parsed_data
        brand = data.get('brand', '')
        model = data.get('model', '')
        year = data.get('year', '')
        price = data.get('price', 0)
        mileage_km = data.get('mileage_km')  # Fixed: use mileage_km
        fuel = data.get('fuel', '')
        gearbox = data.get('gearbox', '')
        
        # Format mileage for display
        if mileage_km:
            mileage_display = f"{mileage_km:,}"
        else:
            mileage_display = "N/A"
        
        # Calculate discount
        discount_pct = ((avg_price - price) / avg_price) * 100 if avg_price else 0
        
        # Build message (Telegram supports HTML and Markdown)
        message = f"""
🎯 <b>ОФЕРТА</b> - Оценка: {score:.1f}/10

🚗 <b>{brand} {model}</b> ({year})
💰 <b>Цена</b>: {price:,.0f} BGN
📊 <b>Средна пазарна цена</b>: {avg_price:,.0f} BGN
💵 <b>Отстъпка</b>: {discount_pct:.1f}% ({(avg_price - price):,.0f} BGN по-евтино!)
📏 <b>Пробег</b>: {mileage_display} км
⛽ <b>Гориво</b>: {fuel}
⚙️ <b>Скоростна кутия</b>: {gearbox}
📈 <b>Базирано на</b>: {comp_count} подобни обяви

🔗 <a href="{listing.url}">Виж обявата тук</a>
"""
        
        logger.info(f"📢 Posting to Telegram: {brand} {model} {year} - {score:.1f}/10")
        
        # Send message using Telegram Bot API
        telegram_api_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        
        response = requests.post(
            telegram_api_url,
            json={
                'chat_id': settings.TELEGRAM_CHANNEL_ID,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': False
            },
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Posted to Telegram successfully")
            return True
        else:
            logger.error(f"❌ Telegram API error: {response.status_code} - {response.text}")
            return False
        
    except Exception as e:
        logger.error(f"Error posting to Telegram: {e}")
        return False

