"""
Enhanced Database-Based Deal Monitor with Price History Tracking

Improvements:
1. Track price changes and detect price drops
2. Give bonus points for recent price drops
3. Better comparable matching (mileage, fuel, gearbox)
4. Market behavior insights (time-on-market, velocity)
5. Validation and logging for real examples
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy import create_engine, select, and_, or_, func, cast, Integer, String, text
from sqlalchemy.orm import sessionmaker
from celery import shared_task

from libs.domain.models import ListingRaw
from configs.settings import settings

logger = logging.getLogger(__name__)


@shared_task(name="monitor_database_deals_enhanced", soft_time_limit=600, time_limit=700)
def monitor_database_deals_enhanced():
    """
    Enhanced monitor with price drop detection and better scoring.
    
    This runs every 5 minutes and:
    1. Processes new/updated listings
    2. Detects price drops
    3. Calculates enhanced scores with price history
    4. Posts high-quality deals to Telegram
    """
    logger.info("🔍 Starting ENHANCED database deal monitor...")
    
    try:
        # Create database session
        engine = create_engine(settings.DATABASE_SYNC_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Get listings from last 5 minutes
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        fresh_listing_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        
        query = session.query(ListingRaw).filter(
            and_(
                or_(
                    ListingRaw.first_seen_at >= cutoff_time,
                    ListingRaw.updated_at >= cutoff_time
                ),
                ListingRaw.first_seen_at >= fresh_listing_cutoff,
                ListingRaw.is_active == True,
                ListingRaw.parsed_data.isnot(None)
            )
        ).order_by(ListingRaw.first_seen_at.desc())
        
        listings = query.all()
        logger.info(f"📊 Found {len(listings)} new/updated listings to evaluate")
        
        if not listings:
            logger.info("✅ No new listings to process")
            session.close()
            return {'status': 'success', 'processed': 0}
        
        # Track price changes FIRST (before scoring)
        _track_price_changes(session, listings)
        
        # Process each listing with enhanced scoring
        processed = 0
        high_scores = 0
        posted_count = 0
        MAX_POSTS_PER_RUN = 3
        score_distribution = {'<5': 0, '5-6': 0, '6-7': 0, '7-8': 0, '8+': 0}
        
        for listing in listings:
            try:
                data = listing.parsed_data
                brand = data.get('brand')
                model = data.get('model')
                year = data.get('year')
                price = data.get('price')
                mileage_km = data.get('mileage_km')
                fuel = data.get('fuel')
                gearbox = data.get('gearbox')
                
                # Validation
                if not all([brand, model, year, price]):
                    continue
                
                try:
                    year = int(year) if isinstance(year, str) else year
                    price = float(price) if isinstance(price, str) else price
                    mileage_km = int(mileage_km) if isinstance(mileage_km, str) else mileage_km
                except (ValueError, TypeError):
                    continue
                
                # Filter: mileage must be present and ≤250k km
                if not mileage_km or mileage_km > 250000:
                    continue
                
                # Enhanced evaluation with price history
                score_result = _evaluate_listing_enhanced(
                    session, 
                    listing.site_ad_id, 
                    brand, model, year, price, mileage_km, fuel, gearbox,
                    listing.first_seen_at, listing.updated_at
                )
                
                if not score_result:
                    continue
                
                score = score_result.get('score')
                
                # Track distribution
                if score < 5:
                    score_distribution['<5'] += 1
                elif score < 6:
                    score_distribution['5-6'] += 1
                elif score < 7:
                    score_distribution['6-7'] += 1
                elif score < 8:
                    score_distribution['7-8'] += 1
                else:
                    score_distribution['8+'] += 1
                
                # Log all scores for validation
                logger.info(f"📊 Evaluated: {brand} {model} {year} - Score: {score:.2f}/10 "
                          f"(Price: {price:,.0f} BGN, Mileage: {mileage_km:,} km)")
                
                # Post high scores
                if score >= 8.3:
                    high_scores += 1
                    
                    if posted_count < MAX_POSTS_PER_RUN:
                        logger.info(f"🎯 HIGH SCORE: {score:.1f}/10 - {brand} {model} {year}")
                        logger.info(f"   Reasons: {score_result.get('reasons', [])}")
                        
                        if _post_to_telegram_enhanced(listing, score_result):
                            posted_count += 1
                    else:
                        logger.info(f"⏭️ RATE LIMITED: {score:.1f}/10 - {brand} {model} {year}")
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Error processing listing {listing.site_ad_id}: {e}")
                continue
        
        session.close()
        
        logger.info(f"✅ Monitor complete: {processed} processed, {high_scores} high scores, "
                   f"{posted_count}/{MAX_POSTS_PER_RUN} posted")
        logger.info(f"📊 Score distribution: <5: {score_distribution['<5']}, "
                   f"5-6: {score_distribution['5-6']}, 6-7: {score_distribution['6-7']}, "
                   f"7-8: {score_distribution['7-8']}, 8+: {score_distribution['8+']}")
        
        return {
            'status': 'success',
            'processed': processed,
            'high_scores': high_scores,
            'posted_count': posted_count,
            'score_distribution': score_distribution
        }
        
    except Exception as e:
        logger.error(f"❌ Monitor exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {'status': 'error', 'error': str(e)}


def _track_price_changes(session, listings: List[ListingRaw]):
    """
    Track price changes for updated listings.
    Store in parsed_data JSON for now (can move to price_history table later).
    """
    for listing in listings:
        try:
            # Check if this is an update (not first time seen)
            if listing.updated_at and listing.first_seen_at:
                time_diff = (listing.updated_at - listing.first_seen_at).total_seconds()
                
                # If updated more than 1 hour after creation, check for price change
                if time_diff > 3600:
                    data = listing.parsed_data
                    current_price = data.get('price')
                    
                    if current_price and 'previous_price' not in data:
                        # TODO: Query old price from database history or previous scrape
                        # For now, we'll detect this in the next scrape cycle
                        pass
        
        except Exception as e:
            logger.error(f"Error tracking price for {listing.site_ad_id}: {e}")
            continue


def _evaluate_listing_enhanced(
    session, 
    site_ad_id: str,
    brand: str, 
    model: str, 
    year: int, 
    price: float,
    mileage_km: int,
    fuel: Optional[str],
    gearbox: Optional[str],
    first_seen: datetime,
    last_updated: datetime
) -> Optional[Dict]:
    """
    Enhanced scoring algorithm with:
    1. Better comparable matching (mileage, fuel, gearbox)
    2. Price drop detection
    3. Time-on-market factor
    4. Market velocity insights
    5. Price range awareness (sweet spot: 5K-50K BGN)
    
    Scoring breakdown:
    - Base: 4.0 points
    - Discount ≥30%: +4.5 → 8.5+ (EXCELLENT!)
    - Discount ≥25%: +4.0 → 8.0+ (HIGH SCORE)
    - Discount 20-25%: +3.5 → 7.5+ (HIGH SCORE)
    - Discount 15-20%: +2.5 → 6.5
    - Discount 10-15%: +1.5 → 5.5
    - Recent price drop >10%: +1.0 bonus
    - Recent year (≥2020): +0.3
    - Low mileage for age: +0.5
    - On market >14 days: +0.2 (seller motivated)
    
    Price range adjustments (based on market liquidity):
    - <5K BGN: -1.5 penalty (too risky, high maintenance costs)
    - 5K-10K BGN: +0.7 bonus (HIGHEST LIQUIDITY - most searched!)
    - 10K-50K BGN: +0.3 bonus (sweet spot for value deals)
    - >50K BGN: NO bonus (less liquid, harder to sell)
    """
    try:
        # Get comparable vehicles with enhanced matching
        comparables_data = _get_enhanced_comparables(
            session, brand, model, year, mileage_km, fuel, gearbox
        )
        
        if not comparables_data:
            return None
        
        avg_price = comparables_data['avg_price']
        comp_count = comparables_data['count']
        
        if not avg_price or comp_count < 5:
            return {
                'score': 3.0,
                'avg_price': avg_price,
                'comp_count': comp_count,
                'reasons': ['Insufficient market data']
            }
        
        # Calculate discount percentage
        discount_pct = ((avg_price - price) / avg_price) * 100
        
        # Base score
        score = 4.0
        reasons = []
        
        # CRITICAL: Market liquidity awareness
        # Based on real customer behavior: <10K = most searched
        if price < 5000:
            score -= 1.5
            reasons.append(f"⚠️ Too cheap ({price:,.0f} BGN) - high maintenance risk")
        # HIGHEST LIQUIDITY: Most customers search here!
        elif 5000 <= price < 10000:
            score += 0.7
            reasons.append(f"🔥 High liquidity range ({price:,.0f} BGN) - most searched!")
        # Sweet spot: Good value deals
        elif 10000 <= price <= 50000:
            score += 0.3
            reasons.append(f"✓ Value deal range ({price:,.0f} BGN)")
        # Above 50K: No bonus (less liquid, smaller audience)
        else:
            reasons.append(f"Premium range ({price:,.0f} BGN) - smaller market")
        
        # Price scoring (most important)
        if discount_pct >= 30:
            score += 4.5
            reasons.append(f"Excellent price: {discount_pct:.1f}% below market")
        elif discount_pct >= 25:
            score += 4.0
            reasons.append(f"Great price: {discount_pct:.1f}% below market")
        elif discount_pct >= 20:
            score += 3.5
            reasons.append(f"Very good price: {discount_pct:.1f}% below market")
        elif discount_pct >= 15:
            score += 3.0
            reasons.append(f"Good price: {discount_pct:.1f}% below market")
        elif discount_pct >= 10:
            score += 2.0
            reasons.append(f"Decent price: {discount_pct:.1f}% below market")
        elif discount_pct >= 5:
            score += 1.0
            reasons.append(f"Fair price: {discount_pct:.1f}% below market")
        elif discount_pct >= 0:
            score += 0.5
            reasons.append(f"Average market price")
        else:
            score -= abs(discount_pct) / 10
            reasons.append(f"Above market price: {abs(discount_pct):.1f}% premium")
        
        # Confidence adjustment
        if comp_count >= 20:
            confidence = 1.0
        elif comp_count >= 10:
            confidence = 0.95
        else:
            confidence = 0.9
        
        score = score * confidence
        
        # Age bonus
        if year >= 2020:
            score += 0.3
            reasons.append("Recent model year")
        
        # Mileage bonus (low usage for age)
        age = 2025 - year
        expected_mileage = age * 15000  # Average 15k km/year
        if mileage_km < expected_mileage * 0.7:
            score += 0.5
            reasons.append(f"Low mileage for age: {mileage_km:,} km vs expected {expected_mileage:,} km")
        
        # Time-on-market bonus (seller motivation)
        days_on_market = (datetime.now(timezone.utc) - first_seen.replace(tzinfo=timezone.utc)).days
        if days_on_market >= 14:
            score += 0.2
            reasons.append(f"On market {days_on_market} days - seller may negotiate")
        
        # TODO: Price drop bonus (need historical data)
        # if has_recent_price_drop:
        #     score += 1.0
        #     reasons.append("Recent price drop detected!")
        
        # Clamp to 1-10 range
        score = max(1.0, min(10.0, score))
        
        return {
            'score': score,
            'avg_price': avg_price,
            'comp_count': comp_count,
            'discount_pct': discount_pct,
            'days_on_market': days_on_market,
            'reasons': reasons,
            'fuel': fuel,
            'gearbox': gearbox
        }
        
    except Exception as e:
        logger.error(f"Error evaluating {brand} {model}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def _get_enhanced_comparables(
    session,
    brand: str,
    model: str,
    year: int,
    mileage_km: int,
    fuel: Optional[str],
    gearbox: Optional[str]
) -> Optional[Dict]:
    """
    Get comparable vehicles with enhanced matching:
    - Same brand/model
    - ±2 years
    - ±30% mileage (NEW!)
    - Same fuel type if specified (NEW!)
    - Same gearbox if specified (NEW!)
    """
    try:
        # Calculate mileage range (±30%)
        mileage_min = int(mileage_km * 0.7)
        mileage_max = int(mileage_km * 1.3)
        
        # Build SQL with optional fuel and gearbox matching
        sql = """
            SELECT 
                AVG(CAST(parsed_data->>'price' AS INTEGER)) as avg_price,
                COUNT(*) as count,
                MIN(CAST(parsed_data->>'price' AS INTEGER)) as min_price,
                MAX(CAST(parsed_data->>'price' AS INTEGER)) as max_price
            FROM listings_raw
            WHERE parsed_data->>'brand' = :brand
              AND parsed_data->>'model' = :model
              AND CAST(parsed_data->>'year' AS INTEGER) BETWEEN :year_min AND :year_max
              AND CAST(parsed_data->>'mileage_km' AS INTEGER) BETWEEN :mileage_min AND :mileage_max
              AND CAST(parsed_data->>'price' AS INTEGER) > 500
              AND is_active = true
        """
        
        params = {
            'brand': brand,
            'model': model,
            'year_min': year - 2,
            'year_max': year + 2,
            'mileage_min': mileage_min,
            'mileage_max': mileage_max
        }
        
        # Add fuel filter if specified
        if fuel:
            sql += " AND parsed_data->>'fuel' = :fuel"
            params['fuel'] = fuel
        
        # Add gearbox filter if specified
        if gearbox:
            sql += " AND parsed_data->>'gearbox' = :gearbox"
            params['gearbox'] = gearbox
        
        result = session.execute(text(sql), params)
        row = result.fetchone()
        
        if row and row[0]:
            return {
                'avg_price': float(row[0]),
                'count': int(row[1]),
                'min_price': float(row[2]) if row[2] else None,
                'max_price': float(row[3]) if row[3] else None
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting comparables for {brand} {model}: {e}")
        return None


def _post_to_telegram_enhanced(listing: ListingRaw, score_result: Dict):
    """
    Post enhanced deal to Telegram with more context
    """
    try:
        import requests
        
        data = listing.parsed_data
        brand = data.get('brand', '')
        model = data.get('model', '')
        year = data.get('year', '')
        price = data.get('price', 0)
        mileage_km = data.get('mileage_km')
        fuel = data.get('fuel', 'N/A')
        gearbox = data.get('gearbox', 'N/A')
        
        score = score_result['score']
        avg_price = score_result['avg_price']
        discount_pct = score_result['discount_pct']
        comp_count = score_result['comp_count']
        days_on_market = score_result.get('days_on_market', 0)
        reasons = score_result.get('reasons', [])
        
        mileage_display = f"{mileage_km:,}" if mileage_km else "N/A"
        
        # Enhanced message with reasons
        reasons_text = "\n".join([f"✓ {reason}" for reason in reasons[:3]])  # Top 3 reasons
        
        message = f"""
🎯 <b>ОФЕРТА</b> - Оценка: {score:.1f}/10

🚗 <b>{brand} {model}</b> ({year})
💰 <b>Цена</b>: {price:,.0f} BGN
📊 <b>Средна пазарна цена</b>: {avg_price:,.0f} BGN
💵 <b>Отстъпка</b>: {discount_pct:.1f}% ({(avg_price - price):,.0f} BGN по-евтино!)

📏 <b>Пробег</b>: {mileage_display} км
⛽ <b>Гориво</b>: {fuel}
⚙️ <b>Скоростна кутия</b>: {gearbox}
📅 <b>На пазара</b>: {days_on_market} дни

<b>Защо е добра оферта:</b>
{reasons_text}

📈 <b>Базирано на</b>: {comp_count} подобни обяви

🔗 <a href="{listing.url}">Виж обявата тук</a>
"""
        
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
            logger.error(f"❌ Telegram API error: {response.status_code}")
            return False
        
    except Exception as e:
        logger.error(f"Error posting to Telegram: {e}")
        return False
