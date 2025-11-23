"""
Celery app entry point - imports all task modules to register them
"""
from workers.pipeline.celery_app import celery_app

# Import core task modules to register them with Celery
# This ensures tasks are discoverable when workers start
try:
    from workers.pipeline.tasks import (
        parse,
        normalize,
        dedupe,
        price,
        ai,
        score,
        simple_score,
        notify,
        monitor_tasks,
        database_monitor,
        database_monitor_enhanced,
        market_score,  # NEW: Market-aware scoring system
    )
except ImportError as e:
    print(f"Warning: Some task modules could not be imported: {e}")
    # Import essential modules only
    from workers.pipeline.tasks import (
        market_score,
        notify,
        monitor_tasks,
    )

__all__ = ["celery_app"]
