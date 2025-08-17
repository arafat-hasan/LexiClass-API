"""Celery application configuration for LexiClass API."""

from celery import Celery
from lexiclass_worker.core.queue_config import (
    QUEUE_CONFIGS,
    TASK_QUEUES,
    TASK_ROUTES,
    QueueName,
)

# Create Celery app
app = Celery("lexiclass_api")

# Configure Celery
app.conf.update(
    broker_url="redis://localhost:6379/0",  # Default Redis broker URL
    result_backend="redis://localhost:6379/0",  # Default Redis result backend
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    enable_utc=True,
    task_track_started=True,
    
    # Use shared queue configuration
    task_queues=TASK_QUEUES,
    task_routes=TASK_ROUTES,
    
    # Add task-specific settings from queue configs
    task_annotations={
        f"lexiclass_api.tasks.{queue.name}_task": {
            "rate_limit": queue.rate_limit,
            "retry_backoff": True,
            "retry_backoff_max": queue.retry_policy["interval_max"],
            "retry_jitter": True,
            "max_retries": queue.retry_policy["max_retries"],
            "retry_delay": queue.retry_policy["interval_start"],
            "retry_kwargs": {"max_delay": queue.retry_policy["interval_max"]},
        } for queue in QUEUE_CONFIGS.values()
    },
)
