"""Prediction tasks."""

import logging
from typing import Dict, List, Optional
from uuid import uuid4

from celery import Task

from lexiclass_worker.core.queue_config import QueueName

from ..db.session import async_session
from ..services.documents import DocumentService
from ..services.projects import ProjectService
from ..worker import celery_app

logger = logging.getLogger(__name__)


class PredictionTask(Task):
    """Base task for prediction operations."""

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
    base=PredictionTask,
    bind=True,
    queue=QueueName.PREDICTION,
)
async def predict_documents(
    self,
    project_id: str,
    document_ids: Optional[List[str]] = None,
    prediction_id: Optional[str] = None,
) -> dict:
    """Make predictions for documents.

    Args:
        project_id: Project ID
        document_ids: Optional list of document IDs to predict
        prediction_id: Optional prediction ID

    Returns:
        Task result with prediction statistics
    """
    try:
        # Get project
        project = await self.project_service.get(project_id)
        if not project:
            raise ValueError("Project not found")

        # Check if model is ready
        if project.model_status != "ready":
            raise ValueError("Model not ready for predictions")

        # Generate prediction ID if not provided
        prediction_id = prediction_id or str(uuid4())

        # Get documents to predict
        if document_ids:
            documents = await self.doc_service.get_multi_by_ids(project_id, document_ids)
            if len(documents) != len(document_ids):
                raise ValueError("One or more documents not found")
        else:
            documents = await self.doc_service.get_multi(
                project_id=project_id,
                status="indexed",  # Only predict indexed documents
            )

        if not documents:
            return {
                "prediction_id": prediction_id,
                "status": "failed",
                "message": "No documents available for prediction",
            }

        try:
            # TODO: Implement actual prediction logic here
            # This would typically involve:
            # 1. Load model
            # 2. Preprocess documents
            # 3. Make predictions
            # 4. Update documents with predictions
            # For now, we'll just simulate predictions

            # Update documents with predictions
            for doc in documents:
                doc.prediction = "class_a"  # Simulated prediction
                doc.confidence = 0.95  # Simulated confidence
                doc.prediction_id = prediction_id
            await self.doc_service.db.commit()

            return {
                "prediction_id": prediction_id,
                "status": "completed",
                "message": "Predictions completed successfully",
                "total_documents": len(documents),
                "model_version": project.model_version,
            }

        except Exception as e:
            # Reset prediction info on failure
            for doc in documents:
                doc.prediction = None
                doc.confidence = None
                doc.prediction_id = None
            await self.doc_service.db.commit()
            raise e

    except Exception as e:
        logger.exception("Prediction failed")
        return {
            "prediction_id": prediction_id,
            "status": "failed",
            "message": str(e),
        }
    finally:
        await self.project_service.db.close()
        await self.doc_service.db.close()
