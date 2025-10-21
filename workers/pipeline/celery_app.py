"""
Celery application configuration
"""
from celery import Celery
from celery.schedules import crontab

from configs.settings import settings

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
    "scrape-mobile-bg-every-2-minutes": {
        "task": "workers.scrape.tasks.scrape_mobile_bg",
        "schedule": crontab(minute="*/2"),
    },
    "scrape-cars-bg-every-3-minutes": {
        "task": "workers.scrape.tasks.scrape_cars_bg",
        "schedule": crontab(minute="*/3"),
    },
    "rescore-listings-hourly": {
        "task": "workers.pipeline.tasks.score.rescore_stale_listings",
        "schedule": crontab(minute=0),
    },
    "validate-data-quality-daily": {
        "task": "workers.pipeline.tasks.housekeeping.validate_data_quality",
        "schedule": crontab(hour=3, minute=0),
    },
}
