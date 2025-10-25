"""Celery application configuration for LexiClass API."""

from typing import Dict, Any

from celery import Celery
from lexiclass_core.queue_config import (
    QUEUE_CONFIGS,
    TASK_QUEUES,
    TASK_ROUTES,
)

from lexiclass_api.core.config import settings


def get_task_annotations() -> Dict[str, Dict[str, Any]]:
    """Get task-specific annotations from queue configs."""
    return {
        f"lexiclass_api.tasks.{queue.name}_task": {
            "rate_limit": queue.rate_limit,
            "retry_backoff": True,
            "retry_backoff_max": queue.retry_policy["interval_max"],
            "retry_jitter": True,
            "max_retries": queue.retry_policy["max_retries"],
            "retry_delay": queue.retry_policy["interval_start"],
            "retry_kwargs": {"max_delay": queue.retry_policy["interval_max"]},
        } for queue in QUEUE_CONFIGS.values()
    }


# Create Celery app
app = Celery("lexiclass_api")

# Configure Celery
app.conf.update(
    # Broker and result backend
    broker_url=str(settings.CELERY_BROKER_URL),
    result_backend=str(settings.CELERY_RESULT_BACKEND),
    
    # Serialization
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    
    # General settings
    enable_utc=settings.CELERY_ENABLE_UTC,
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_retry_backoff=settings.CELERY_TASK_RETRY_BACKOFF,
    task_retry_jitter=settings.CELERY_TASK_RETRY_JITTER,
    task_default_rate_limit=settings.CELERY_TASK_DEFAULT_RATE_LIMIT,
    task_default_retry_delay=settings.CELERY_TASK_DEFAULT_RETRY_DELAY,
    task_max_retries=settings.CELERY_TASK_MAX_RETRIES,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
    worker_send_task_events=settings.CELERY_WORKER_SEND_TASK_EVENTS,
    
    # Queue configuration
    task_queues=TASK_QUEUES,
    task_routes=TASK_ROUTES,
    
    # Task-specific settings
    task_annotations=get_task_annotations(),
)
