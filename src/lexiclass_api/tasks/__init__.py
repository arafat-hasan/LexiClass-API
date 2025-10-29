"""Celery tasks module for LexiClass API.

Note: Task implementations have been moved to LexiClass-Worker.
This module is kept for backwards compatibility but no longer exports tasks.
The API should use the WorkerClient from core.worker to submit tasks to the worker service.
"""

__all__ = []
