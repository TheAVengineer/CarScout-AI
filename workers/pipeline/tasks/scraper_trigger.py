"""
Celery tasks for triggering Scrapy spiders
"""
import subprocess
import logging
from pathlib import Path

from workers.pipeline.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="trigger_fresh_deals_spider", 
    bind=True,
    time_limit=None,  # No time limit for long-running spider
    soft_time_limit=None,  # No soft time limit either
)
def trigger_fresh_deals_spider(self, continuous_mode=True):
    """
    Trigger the Mobile.bg fresh deals spider (sort=7 - last 2 days)
    
    This spider scrapes at brand level (131 brands) with the sort=7 filter,
    which shows only listings from the last 2 days. This is 10x faster than
    model-by-model scraping and ensures 100% fresh listings.
    
    Args:
        continuous_mode: If True, runs in infinite loop scanning all brands repeatedly
                        If False, runs once and exits
    
    Expected results (continuous mode):
    - Runtime: Infinite (until stopped)
    - Cycle time: ~11 hours per full scan (131 brands × 5 min/brand)
    - Listings found: ~20,000+ per cycle
    - Deal detection: Real-time (2-4 hour latency max)
    """
    try:
        # Get project root (2 levels up from tasks dir)
        project_root = Path(__file__).parent.parent.parent.parent
        scrape_dir = project_root / "workers" / "scrape"
        venv_python = project_root / ".venv" / "bin" / "python"
        
        mode = "CONTINUOUS" if continuous_mode else "SINGLE-RUN"
        logger.info(f"🚀 Starting fresh deals spider in {mode} mode")
        logger.info(f"   Project root: {project_root}")
        logger.info(f"   Scrape dir: {scrape_dir}")
        if continuous_mode:
            logger.info(f"   Mode: Continuous scanning (infinite loop)")
            logger.info(f"   Cycle time: ~11 hours per full scan")
            logger.info(f"   Will keep running until manually stopped")
        else:
            logger.info(f"   Mode: Single run (one pass through all brands)")
            logger.info(f"   Expected runtime: ~11 hours")
        
        # Run spider as subprocess
        cmd = [
            str(venv_python),
            "-m", "scrapy",
            "crawl", "mobile_bg_fresh_deals",
            "-s", "LOG_LEVEL=INFO",
            "-s", "CONCURRENT_REQUESTS=4",  # Limit concurrency
            "-s", "DOWNLOAD_DELAY=1",  # Be nice to Mobile.bg
        ]
        
        # Add continuous mode flag
        if continuous_mode:
            cmd.extend(["-a", "continuous=true"])
        
        # No timeout for continuous mode (runs forever)
        timeout = None if continuous_mode else 14400
        
        # Run spider - let it log to stdout/stderr naturally (don't capture)
        result = subprocess.Popen(
            cmd,
            cwd=str(scrape_dir),
            stdout=subprocess.DEVNULL,  # Suppress stdout to avoid memory issues
            stderr=subprocess.DEVNULL,  # Suppress stderr
        )
        
        # Wait for process to complete (or run forever in continuous mode)
        if continuous_mode:
            logger.info(f"✅ Fresh deals spider started as background process (PID: {result.pid})")
            logger.info(f"   Spider will run continuously until manually stopped")
            return {"status": "started", "pid": result.pid, "mode": "continuous"}
        else:
            result.wait(timeout=timeout)
            if result.returncode == 0:
                logger.info("✅ Fresh deals spider completed successfully")
                return {"status": "success"}
            else:
                logger.error(f"❌ Fresh deals spider failed with code {result.returncode}")
                return {"status": "error", "code": result.returncode}
            
    except Exception as e:
        logger.error(f"💥 Fresh deals spider crashed: {str(e)}")
        return {"status": "error", "error": str(e)}
