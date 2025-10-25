"""Prediction tasks."""

import logging
from typing import Dict, List, Optional
from uuid import uuid4

from celery import Task

from lexiclass_worker.core.queue_config import QueueName

from ..db.session import async_session
from ..models import IndexStatus
from ..schemas.prediction import PredictionCreate
from ..services.documents import DocumentService
from ..services.field_classes import FieldClassService
from ..services.fields import FieldService
from ..services.models import ModelService
from ..services.predictions import PredictionService
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
                index_status=IndexStatus.INDEXED,  # Only predict indexed documents
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


async def _predict_field_async(
    field_id: str,
    document_ids: Optional[List[str]] = None,
    params: Optional[Dict] = None,
) -> dict:
    """Make predictions for documents using a field's model (async implementation).

    Args:
        field_id: Field ID to use for prediction
        document_ids: Optional list of document IDs to predict. If None, predicts all documents in the project.
        params: Optional prediction parameters

    Returns:
        Task result with prediction statistics
    """
    # Import here to avoid circular imports
    from ..db.session import engine

    # Dispose of the engine to ensure fresh connections in the new event loop
    await engine.dispose()

    db = async_session()
    field_service = FieldService(db)
    model_service = ModelService(db)
    prediction_service = PredictionService(db)
    class_service = FieldClassService(db)
    doc_service = DocumentService(db)

    try:
        # Get field
        field = await field_service.get(field_id)
        if not field:
            raise ValueError("Field not found")

        logger.info(
            "Starting field prediction",
            extra={"field_id": field_id, "field_name": field.name, "document_count": len(document_ids)},
        )

        # Get latest ready model for this field
        model = await model_service.get_latest_ready_by_field(field_id)
        if not model:
            raise ValueError("No ready model found for this field")

        # Get documents
        if document_ids:
            # Get specific documents by ID
            documents = []
            for doc_id in document_ids:
                doc = await doc_service.get_by_id(doc_id)
                if doc:
                    documents.append(doc)
            if len(documents) != len(document_ids):
                logger.warning(
                    "Not all documents found",
                    extra={
                        "field_id": field_id,
                        "requested": len(document_ids),
                        "found": len(documents),
                    },
                )
        else:
            # Get all documents for the project
            documents = await doc_service.get_multi(
                project_id=field.project_id,
                limit=10000,  # Set a reasonable limit
            )
            logger.info(
                "Predicting all documents in project",
                extra={
                    "field_id": field_id,
                    "project_id": field.project_id,
                    "document_count": len(documents),
                },
            )

        try:
            # TODO: Implement actual prediction logic here
            # This would typically involve:
            # 1. Load model from storage
            # 2. Preprocess document content
            # 3. Make predictions with confidence scores
            # 4. Store predictions in Prediction table
            #
            # For now, we'll simulate predictions
            logger.info(
                "Making predictions (simulated)",
                extra={"field_id": field_id, "model_id": model.id},
            )

            # Get field classes for simulated predictions
            classes = await class_service.get_by_field(field_id)
            if not classes:
                raise ValueError("No classes found for this field")

            predictions_created = 0
            for doc in documents:
                # Simulate prediction - pick first class
                predicted_class = classes[0]
                simulated_confidence = 0.95

                # Create or update prediction
                prediction_create = PredictionCreate(
                    document_id=doc.id,
                    field_id=field_id,
                    model_id=model.id,
                    class_id=predicted_class.id,
                    confidence=simulated_confidence,
                    pred_metadata={
                        "model_version": model.version,
                        "simulated": True,
                    },
                )

                await prediction_service.create(prediction_create)
                predictions_created += 1

            logger.info(
                "Field prediction completed successfully",
                extra={
                    "field_id": field_id,
                    "model_id": model.id,
                    "predictions_created": predictions_created,
                },
            )

            return {
                "status": "completed",
                "message": "Field predictions completed successfully",
                "model_id": model.id,
                "model_version": model.version,
                "total_documents": len(documents),
                "predictions_created": predictions_created,
            }

        except Exception as e:
            logger.error(
                "Field prediction failed",
                extra={"field_id": field_id, "model_id": model.id, "error": str(e)},
            )
            raise e

    except Exception as e:
        logger.exception("Field prediction task failed")
        return {
            "status": "failed",
            "message": str(e),
        }
    finally:
        await db.close()


@celery_app.task(
    base=PredictionTask,
    bind=True,
    queue=QueueName.PREDICTION,
)
def predict_field(
    self,
    field_id: str,
    document_ids: Optional[List[str]] = None,
    params: Optional[Dict] = None,
) -> dict:
    """Make predictions for documents using a field's model (Celery task wrapper).

    This is a synchronous wrapper that executes the async prediction logic.

    Args:
        field_id: Field ID to use for prediction
        document_ids: Optional list of document IDs to predict
        params: Optional prediction parameters

    Returns:
        Task result with prediction statistics
    """
    import asyncio

    # Run the async function in a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_predict_field_async(field_id, document_ids, params))
        return result
    finally:
        loop.close()
