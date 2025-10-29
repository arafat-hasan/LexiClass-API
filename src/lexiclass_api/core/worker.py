"""Worker client for communicating with LexiClass-Worker service."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol

from celery import Celery
from celery.result import AsyncResult
from pydantic import BaseModel, Field

from .config import settings
from lexiclass_core.queue_config import QUEUE_CONFIGS, TASK_QUEUES, TASK_ROUTES
from lexiclass_core.constants import QueueName, TaskStatus
from lexiclass_core.schemas import (
    IndexDocumentsInput,
    TrainFieldModelInput,
    PredictFieldDocumentsInput,
    TaskResult,
)

logger = logging.getLogger(__name__)


class TaskHandler(Protocol):
    """Protocol for task handlers."""

    @property
    def task_name(self) -> str:
        """Get task name."""
        ...

    def submit(self, input_data: BaseModel) -> AsyncResult:
        """Submit task to worker."""
        ...


class BaseTaskHandler(ABC):
    """Base class for task handlers."""

    def __init__(self, app: Celery) -> None:
        """Initialize task handler.

        Args:
            app: Celery app instance
        """
        self.app = app

    @property
    @abstractmethod
    def task_name(self) -> str:
        """Get task name."""
        ...

    @property
    @abstractmethod
    def input_schema(self) -> type[BaseModel]:
        """Get input schema."""
        ...

    @property
    @abstractmethod
    def queue_name(self) -> QueueName:
        """Get queue name."""
        ...

    def submit(self, input_data: BaseModel) -> AsyncResult:
        """Submit task to worker.

        Args:
            input_data: Task input data

        Returns:
            Celery AsyncResult for tracking task status
        """
        # Validate input data
        if not isinstance(input_data, self.input_schema):
            raise ValueError(f"Invalid input data type. Expected {self.input_schema.__name__}")

        # Get queue config
        queue_config = QUEUE_CONFIGS[self.queue_name]

        # Submit task
        return self.app.send_task(
            self.task_name,
            kwargs=input_data.model_dump(),
            queue=queue_config.name.value,  # Use .value to get string from enum
            routing_key=queue_config.routing_key,
            priority=queue_config.priority,
            retry=True,
            retry_policy=queue_config.retry_policy,
            rate_limit=queue_config.rate_limit,
        )


class IndexingTaskHandler(BaseTaskHandler):
    """Handler for document indexing tasks."""

    @property
    def task_name(self) -> str:
        """Get task name."""
        return "lexiclass_worker.tasks.index.index_documents_task"

    @property
    def input_schema(self) -> type[BaseModel]:
        """Get input schema."""
        return IndexDocumentsInput

    @property
    def queue_name(self) -> QueueName:
        """Get queue name."""
        return QueueName.INDEXING


class FieldTrainingTaskHandler(BaseTaskHandler):
    """Handler for field model training tasks."""

    @property
    def task_name(self) -> str:
        """Get task name."""
        return "lexiclass_worker.tasks.field_train.train_field_model_task"

    @property
    def input_schema(self) -> type[BaseModel]:
        """Get input schema."""
        return TrainFieldModelInput

    @property
    def queue_name(self) -> QueueName:
        """Get queue name."""
        return QueueName.TRAINING


class FieldPredictionTaskHandler(BaseTaskHandler):
    """Handler for field prediction tasks."""

    @property
    def task_name(self) -> str:
        """Get task name."""
        return "lexiclass_worker.tasks.field_predict.predict_field_documents_task"

    @property
    def input_schema(self) -> type[BaseModel]:
        """Get input schema."""
        return PredictFieldDocumentsInput

    @property
    def queue_name(self) -> QueueName:
        """Get queue name."""
        return QueueName.PREDICTION


class WorkerClient:
    """Client for interacting with LexiClass-Worker service."""

    def __init__(self) -> None:
        """Initialize worker client."""
        self.app = Celery(
            "lexiclass_worker",
            broker=str(settings.CELERY_BROKER_URL),
            backend=str(settings.CELERY_RESULT_BACKEND),
        )
        
        # Configure Celery with shared queue configuration
        self.app.conf.update(
            task_queues=TASK_QUEUES,
            task_routes=TASK_ROUTES,
            task_serializer="json",
            result_serializer="json",
            accept_content=["json"],
            enable_utc=True,
            task_track_started=True,
        )

        # Initialize task handlers
        self._indexing = IndexingTaskHandler(self.app)
        self._field_training = FieldTrainingTaskHandler(self.app)
        self._field_prediction = FieldPredictionTaskHandler(self.app)

    def index_documents(
        self,
        project_id: str,
        documents_path: str,
        is_incremental: bool = True,
    ) -> AsyncResult:
        """Submit document indexing task to worker.

        Args:
            project_id: Project ID
            documents_path: Path to project's document storage directory
            is_incremental: Whether to perform incremental indexing

        Returns:
            Celery AsyncResult for tracking task status
        """
        input_data = IndexDocumentsInput(
            project_id=project_id,
            documents_path=documents_path,
            is_incremental=is_incremental,
        )
        return self._indexing.submit(input_data)

    def train_field_model(
        self,
        field_id: str,
        project_id: str,
    ) -> AsyncResult:
        """Submit field model training task to worker.

        Args:
            field_id: Field ID to train
            project_id: Project ID

        Returns:
            Celery AsyncResult for tracking task status
        """
        input_data = TrainFieldModelInput(
            field_id=field_id,
            project_id=project_id,
        )
        return self._field_training.submit(input_data)

    def predict_field_documents(
        self,
        field_id: str,
        project_id: str,
        document_ids: List[str],
    ) -> AsyncResult:
        """Submit field prediction task to worker.

        Args:
            field_id: Field ID to use for prediction
            project_id: Project ID
            document_ids: List of document IDs to predict

        Returns:
            Celery AsyncResult for tracking task status
        """
        input_data = PredictFieldDocumentsInput(
            field_id=field_id,
            project_id=project_id,
            document_ids=document_ids,
        )
        return self._field_prediction.submit(input_data)

    def get_task_status(self, task_id: str) -> TaskResult:
        """Get task status from worker.

        Args:
            task_id: Task ID to check

        Returns:
            Task status information
        """
        result = AsyncResult(task_id, app=self.app)
        return TaskResult(
            task_id=task_id,
            status=TaskStatus(result.status),
            error=str(result.result) if result.failed() else None,
            result=result.result if result.successful() else None,
        )


# Global worker client instance
worker = WorkerClient()