"""Worker client for communicating with LexiClass-Worker service."""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol

from celery import Celery
from celery.result import AsyncResult
from pydantic import BaseModel, Field

from .config import settings
from lexiclass_core.queue_config import QUEUE_CONFIGS, TASK_QUEUES, TASK_ROUTES
from lexiclass_core.constants import QueueName

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task status enum."""

    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class TaskResult(BaseModel):
    """Base task result schema."""

    task_id: str
    status: TaskStatus
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class TaskInput(BaseModel):
    """Base task input schema."""

    project_id: str = Field(..., description="Project ID")


class IndexingInput(TaskInput):
    """Input schema for document indexing task."""

    documents_path: str = Field(..., description="Path to project's document storage directory")
    is_incremental: bool = Field(True, description="Whether to perform incremental indexing")


class TrainingInput(TaskInput):
    """Input schema for model training task."""

    labels_path: str = Field(..., description="Path to labels file")
    document_ids: Optional[List[str]] = Field(None, description="Optional list of document IDs to train on")
    model_params: Optional[Dict[str, Any]] = Field(None, description="Optional model parameters")


class PredictionInput(TaskInput):
    """Input schema for prediction task."""

    document_ids: List[str] = Field(..., description="List of document IDs to predict")
    model_id: Optional[str] = Field(None, description="Optional model ID to use for prediction")


class TaskHandler(Protocol):
    """Protocol for task handlers."""

    @property
    def task_name(self) -> str:
        """Get task name."""
        ...

    def submit(self, input_data: TaskInput) -> AsyncResult:
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
    def input_schema(self) -> type[TaskInput]:
        """Get input schema."""
        ...

    @property
    @abstractmethod
    def queue_name(self) -> QueueName:
        """Get queue name."""
        ...

    def submit(self, input_data: TaskInput) -> AsyncResult:
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
    def input_schema(self) -> type[TaskInput]:
        """Get input schema."""
        return IndexingInput

    @property
    def queue_name(self) -> QueueName:
        """Get queue name."""
        return QueueName.INDEXING


class TrainingTaskHandler(BaseTaskHandler):
    """Handler for model training tasks."""

    @property
    def task_name(self) -> str:
        """Get task name."""
        return "lexiclass_worker.tasks.train_model_task"

    @property
    def input_schema(self) -> type[TaskInput]:
        """Get input schema."""
        return TrainingInput

    @property
    def queue_name(self) -> QueueName:
        """Get queue name."""
        return QueueName.TRAINING


class PredictionTaskHandler(BaseTaskHandler):
    """Handler for prediction tasks."""

    @property
    def task_name(self) -> str:
        """Get task name."""
        return "lexiclass_worker.tasks.predict_documents_task"

    @property
    def input_schema(self) -> type[TaskInput]:
        """Get input schema."""
        return PredictionInput

    @property
    def queue_name(self) -> QueueName:
        """Get queue name."""
        return QueueName.PREDICTION


class FieldTrainingInput(TaskInput):
    """Input schema for field model training task."""

    field_id: str = Field(..., description="Field ID to train")


class FieldTrainingTaskHandler(BaseTaskHandler):
    """Handler for field model training tasks."""

    @property
    def task_name(self) -> str:
        """Get task name."""
        return "lexiclass_worker.tasks.field_train.train_field_model_task"

    @property
    def input_schema(self) -> type[TaskInput]:
        """Get input schema."""
        return FieldTrainingInput

    @property
    def queue_name(self) -> QueueName:
        """Get queue name."""
        return QueueName.TRAINING


class FieldPredictionInput(TaskInput):
    """Input schema for field prediction task."""

    field_id: str = Field(..., description="Field ID to use for prediction")
    document_ids: List[str] = Field(..., description="Document IDs to predict")


class FieldPredictionTaskHandler(BaseTaskHandler):
    """Handler for field prediction tasks."""

    @property
    def task_name(self) -> str:
        """Get task name."""
        return "lexiclass_worker.tasks.field_predict.predict_field_documents_task"

    @property
    def input_schema(self) -> type[TaskInput]:
        """Get input schema."""
        return FieldPredictionInput

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
        self._training = TrainingTaskHandler(self.app)
        self._prediction = PredictionTaskHandler(self.app)
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
            storage_path: Path to project's document storage directory
            is_incremental: Whether to perform incremental indexing

        Returns:
            Celery AsyncResult for tracking task status
        """
        input_data = IndexingInput(
            project_id=project_id,
            documents_path=documents_path,
            is_incremental=is_incremental,
        )
        return self._indexing.submit(input_data)

    def train_model(
        self,
        project_id: str,
        labels_path: str,
        document_ids: Optional[List[str]] = None,
        model_params: Optional[Dict[str, Any]] = None,
    ) -> AsyncResult:
        """Submit model training task to worker.

        Args:
            project_id: Project ID
            labels_path: Path to labels file
            document_ids: Optional list of document IDs to train on
            model_params: Optional model parameters

        Returns:
            Celery AsyncResult for tracking task status
        """
        input_data = TrainingInput(
            project_id=project_id,
            labels_path=labels_path,
            document_ids=document_ids,
            model_params=model_params,
        )
        return self._training.submit(input_data)

    def predict_documents(
        self,
        project_id: str,
        document_ids: List[str],
        model_id: Optional[str] = None,
    ) -> AsyncResult:
        """Submit prediction task to worker.

        Args:
            project_id: Project ID
            document_ids: List of document IDs to predict
            model_id: Optional model ID to use for prediction

        Returns:
            Celery AsyncResult for tracking task status
        """
        input_data = PredictionInput(
            project_id=project_id,
            document_ids=document_ids,
            model_id=model_id,
        )
        return self._prediction.submit(input_data)

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
        input_data = FieldTrainingInput(
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
        input_data = FieldPredictionInput(
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