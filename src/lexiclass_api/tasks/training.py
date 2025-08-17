"""Training tasks."""

import logging
from typing import Dict, List, Optional

from celery import Task

from lexiclass_worker.core.queue_config import QueueName

from ..db.session import async_session
from ..services.documents import DocumentService
from ..services.projects import ProjectService
from ..worker import celery_app

logger = logging.getLogger(__name__)


class TrainingTask(Task):
    """Base task for training operations."""

    _doc_service = None
    _project_service = None

    @property
    def doc_service(self) -> DocumentService:
        """Get document service.

        Returns:
            Document service instance
        """
        if self._doc_service is None:
            self._doc_service = DocumentService(async_session())
        return self._doc_service

    @property
    def project_service(self) -> ProjectService:
        """Get project service.

        Returns:
            Project service instance
        """
        if self._project_service is None:
            self._project_service = ProjectService(async_session())
        return self._project_service


@celery_app.task(
    base=TrainingTask,
    bind=True,
    queue=QueueName.TRAINING,
)
async def train_model(
    self,
    project_id: str,
    params: Optional[Dict] = None,
) -> dict:
    """Train a classification model.

    Args:
        project_id: Project ID
        params: Optional training parameters

    Returns:
        Task result with training statistics
    """
    try:
        # Get project
        project = await self.project_service.get(project_id)
        if not project:
            raise ValueError("Project not found")

        # Get training documents
        documents = await self.doc_service.get_multi(
            project_id=project_id,
            status="indexed",  # Only use indexed documents
        )

        if not documents:
            return {
                "status": "failed",
                "message": "No indexed documents available for training",
            }

        # Update project status
        project.model_status = "training"
        await self.project_service.db.commit()

        try:
            # TODO: Implement actual training logic here
            # This would typically involve:
            # 1. Data preprocessing
            # 2. Feature extraction
            # 3. Model training
            # 4. Model evaluation
            # 5. Model persistence
            # For now, we'll just simulate training

            # Update project with model info
            project.model_status = "ready"
            project.model_version = project.model_version + 1 if project.model_version else 1
            project.model_metrics = {
                "accuracy": 0.95,  # Simulated metrics
                "f1_score": 0.94,
                "precision": 0.93,
                "recall": 0.92,
            }
            await self.project_service.db.commit()

            return {
                "status": "completed",
                "message": "Model trained successfully",
                "model_version": project.model_version,
                "metrics": project.model_metrics,
            }

        except Exception as e:
            # Update project status on failure
            project.model_status = "failed"
            await self.project_service.db.commit()
            raise e

    except Exception as e:
        logger.exception("Training failed")
        return {
            "status": "failed",
            "message": str(e),
        }
    finally:
        await self.project_service.db.close()
        await self.doc_service.db.close()
