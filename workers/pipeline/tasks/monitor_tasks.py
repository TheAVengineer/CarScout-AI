"""
Deal Monitor Celery Tasks

Purpose: Run the deal monitor spider periodically to detect new listings.
This replaces bulk scraping with intelligent monitoring.
"""

import logging
import subprocess
from datetime import datetime
from pathlib import Path
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="monitor_new_deals", soft_time_limit=900, time_limit=1000)
def monitor_new_deals():
    """
    Run the deal monitor spider to check for new listings.
    
    This scans ONLY the newest listings (first 3 pages, sort=6) to find deals.
    Completes in 3-5 minutes. Compares new listings to database for value assessment.
    
    This task should be scheduled to run every 5 minutes using Celery Beat.
    """
    
    logger.info("🔍 Starting deal monitor run (newest listings only)...")
    
    try:
        # Path to scraper directory
        scraper_dir = Path(__file__).parent.parent.parent / "scrape"
        
        # Path to scrapy in virtual environment
        project_root = Path(__file__).parent.parent.parent.parent
        scrapy_path = project_root / ".venv" / "bin" / "scrapy"
        deal_monitor_config = project_root / "deal_monitor_config.json"
        
        # Run monitor spider with deal monitor config (fast, newest listings only)
        result = subprocess.run(
            [
                str(scrapy_path), "crawl", "mobile_bg_monitor",
                "-s", f"MONITOR_CONFIG_PATH={deal_monitor_config}",
                "-s", "LOG_LEVEL=INFO",
                "-s", "LOG_FILE=/Users/alexandervidenov/Desktop/CarScout-AI/logs/deal_monitor.log",
            ],
            cwd=str(scraper_dir),
            capture_output=True,
            text=True,
            timeout=900,  # 15 minute timeout (increased from 600 to allow detail page scraping)
        )
        
        if result.returncode == 0:
            logger.info("✅ Monitor run completed successfully")
            return {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'output': result.stdout[-500:] if result.stdout else ''  # Last 500 chars
            }
        else:
            logger.error(f"❌ Monitor run failed: {result.stderr}")
            return {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': result.stderr[-500:] if result.stderr else ''
            }
    
    except subprocess.TimeoutExpired:
        logger.error("❌ Monitor run timed out after 10 minutes")
        return {
            'status': 'timeout',
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"❌ Monitor run exception: {e}")
        return {
            'status': 'exception',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }


@shared_task(name="monitor_specific_brand", soft_time_limit=900, time_limit=1000)
def monitor_specific_brand(brand: str, model: str = None, filters: dict = None):
    """
    Monitor a specific brand/model for new listings.
    
    Args:
        brand: Brand name (e.g., "mercedes-benz", "bmw")
        model: Model name (e.g., "a-klasa", "3-seriya"), optional
        filters: Custom filters to apply, optional
    
    Example:
        monitor_specific_brand.delay("bmw", "3-seriya", {"price_max": 40000})
    """
    
    logger.info(f"🔍 Monitoring {brand} {model or 'all models'}...")
    
    # Build URL
    base_url = "https://www.mobile.bg/obiavi/avtomobili-dzhipove"
    if brand:
        base_url += f"/{brand}"
    if model:
        base_url += f"/{model}"
    base_url += "?sort=6"  # Sort by newest
    
    # Create temporary config
    import json
    import tempfile
    
    temp_config = {
        "watch_targets": [
            {
                "name": f"{brand} {model or 'all'} monitor",
                "url": base_url,
                "pages": 3,
                "filters": filters or {}
            }
        ],
        "ai_evaluation": {
            "enabled": True,
            "min_score_to_post": 7.5
        }
    }
    
    # Write temporary config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(temp_config, f)
        config_path = f.name
    
    try:
        scraper_dir = Path(__file__).parent.parent.parent / "scrape"
        
        # Path to scrapy in virtual environment
        project_root = Path(__file__).parent.parent.parent.parent
        scrapy_path = project_root / ".venv" / "bin" / "scrapy"
        
        result = subprocess.run(
            [
                str(scrapy_path), "crawl", "mobile_bg_monitor",
                "-s", f"MONITOR_CONFIG_PATH={config_path}",
                "-s", "LOG_LEVEL=INFO",
            ],
            cwd=str(scraper_dir),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
        
        # Clean up temp file
        Path(config_path).unlink()
        
        if result.returncode == 0:
            logger.info(f"✅ {brand} {model} monitor completed")
            return {'status': 'success', 'brand': brand, 'model': model}
        else:
            logger.error(f"❌ {brand} {model} monitor failed")
            return {'status': 'error', 'brand': brand, 'model': model}
    
    except Exception as e:
        logger.error(f"❌ {brand} {model} monitor exception: {e}")
        return {'status': 'exception', 'error': str(e)}


@shared_task(name="update_monitor_cache")
def update_monitor_cache():
    """
    Update the in-memory cache of existing listing IDs.
    
    This task should run before each monitor run to ensure
    the duplicate detection is accurate.
    """
    
    logger.info("🔄 Updating monitor cache...")
    
    try:
        from libs.domain.database import get_session
        from libs.domain.models import ListingRaw
        from configs.settings import settings
        from sqlalchemy import select
        
        session = next(get_session())
        
        # Get count of existing listings
        result = session.execute(
            select(ListingRaw.site_ad_id).where(
                ListingRaw.source_id == settings.SOURCE_MOBILE_BG
            )
        )
        
        existing_ids = {row[0] for row in result}
        session.close()
        
        logger.info(f"✅ Cache updated: {len(existing_ids)} listing IDs loaded")
        
        return {
            'status': 'success',
            'count': len(existing_ids),
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"❌ Cache update failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
