"""
Celery application configuration
"""
from celery import Celery
from celery.schedules import crontab
import logging

from configs.settings import settings

# Reduce SQLAlchemy logging noise
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

# Initialize Celery app
celery_app = Celery(
    "carscout",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "workers.pipeline.tasks.parse",
        "workers.pipeline.tasks.normalize",
        "workers.pipeline.tasks.dedupe",
        "workers.pipeline.tasks.price",
        "workers.pipeline.tasks.ai",
        "workers.pipeline.tasks.score",
        "workers.pipeline.tasks.notify",
        "workers.pipeline.tasks.monitor_tasks",  # Legacy spider-based monitoring (broken)
        "workers.pipeline.tasks.database_monitor",  # Database-based monitoring (working)
        "workers.pipeline.tasks.database_monitor_enhanced",  # ENHANCED: Better scoring with price history
        "workers.pipeline.tasks.scraper_trigger",  # Fresh deals spider trigger
        "workers.pipeline.tasks.market_score",  # NEW: Market-aware scoring with comparables & red flags
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Sofia",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=270,  # 4.5 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Queue routing - DISABLED for now (use default 'celery' queue)
# celery_app.conf.task_routes = {
#     "workers.pipeline.tasks.parse.*": {"queue": "parse.extract_fields"},
#     "workers.pipeline.tasks.normalize.*": {"queue": "normalize.apply"},
#     "workers.pipeline.tasks.dedupe.*": {"queue": "dedupe.check"},
#     "workers.pipeline.tasks.price.*": {"queue": "price.estimate"},
#     "workers.pipeline.tasks.ai.*": {"queue": "ai.classify"},
#     "workers.pipeline.tasks.score.*": {"queue": "score.rank_filter"},
#     "workers.pipeline.tasks.notify.*": {"queue": "notify.channel"},
# }

# Scheduled tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    # FRESH DEALS SPIDER runs in continuous mode (started manually, runs forever)
    # No schedule needed - runs in infinite loop scanning all brands repeatedly
    # To start: celery_app.send_task('trigger_fresh_deals_spider')
    # To stop: pkill -f "mobile_bg_fresh_deals"
    
    # MARKET-AWARE SCORING FOR FRESH LISTINGS (runs every 2 hours)
    # Uses database comparables, red flag detection, price brackets
    "score-fresh-listings-market-aware-every-2-hours": {
        "task": "score_fresh_market_aware",
        "schedule": 7200.0,  # 2 hours in seconds
    },
    
    # Legacy monitors (DISABLED - using market-aware system)
    # "monitor-database-deals-enhanced-every-5-minutes": {
    #     "task": "monitor_database_deals_enhanced",
    #     "schedule": 300.0,
    # },
    
    # Original database monitor (disabled - using enhanced version)
    # "monitor-database-deals-every-5-minutes": {
    #     "task": "monitor_database_deals",
    #     "schedule": 300.0,
    # },
    
    # Legacy spider-based monitoring (DISABLED - has Playwright yielding bug)
    # "monitor-new-deals-every-5-minutes": {
    #     "task": "monitor_new_deals",
    #     "schedule": 300.0,
    # },
    
    # Legacy bulk scraping (disabled - use monitor instead)
    # "scrape-mobile-bg-every-2-minutes": {
    #     "task": "workers.scrape.tasks.scrape_mobile_bg",
    #     "schedule": crontab(minute="*/2"),
    # },
    # "scrape-cars-bg-every-3-minutes": {
    #     "task": "workers.scrape.tasks.scrape_cars_bg",
    #     "schedule": crontab(minute="*/3"),
    # },
    
    "rescore-listings-hourly": {
        "task": "workers.pipeline.tasks.score.rescore_stale_listings",
        "schedule": crontab(minute=0),
    },
    "validate-data-quality-daily": {
        "task": "workers.pipeline.tasks.housekeeping.validate_data_quality",
        "schedule": crontab(hour=3, minute=0),
    },
}
