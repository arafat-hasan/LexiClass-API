"""Celery worker configuration."""

from celery import Celery

from .core.config import settings

# Create Celery app
celery_app = Celery(
    "lexiclass_api",
    broker=str(settings.CELERY_BROKER_URL),
    backend=str(settings.CELERY_RESULT_BACKEND),
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['lexiclass_api.tasks'])
