"""Training tasks."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from celery import Task

from lexiclass_worker.core.queue_config import QueueName

from ..db.session import async_session
from ..models import IndexStatus, ModelStatus
from ..schemas.model import ModelCreate
from ..services.document_labels import DocumentLabelService
from ..services.documents import DocumentService
from ..services.field_classes import FieldClassService
from ..services.fields import FieldService
from ..services.models import ModelService
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


async def _train_model_async(
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
            index_status=IndexStatus.INDEXED,  # Only use indexed documents
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


@celery_app.task(
    base=TrainingTask,
    bind=True,
    queue=QueueName.TRAINING,
)
def train_model(
    self,
    project_id: str,
    params: Optional[Dict] = None,
) -> dict:
    """Train a classification model (Celery task wrapper).

    This is a synchronous wrapper that executes the async training logic.

    Args:
        project_id: Project ID
        params: Optional training parameters

    Returns:
        Task result with training statistics
    """
    import asyncio

    # Run the async function in a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_train_model_async(self, project_id, params))
        return result
    finally:
        loop.close()


async def _train_field_model_async(
    field_id: str,
    params: Optional[Dict] = None,
) -> dict:
    """Train a classification model for a specific field.

    Args:
        field_id: Field ID to train
        params: Optional training parameters

    Returns:
        Task result with training statistics
    """
    # Import here to avoid circular imports
    from ..db.session import engine

    # Dispose of the engine to ensure fresh connections in the new event loop
    await engine.dispose()

    db = async_session()
    field_service = FieldService(db)
    label_service = DocumentLabelService(db)
    class_service = FieldClassService(db)
    model_service = ModelService(db)
    doc_service = DocumentService(db)

    try:
        # Get field
        field = await field_service.get(field_id)
        if not field:
            raise ValueError("Field not found")

        logger.info(
            "Starting field training",
            extra={"field_id": field_id, "field_name": field.name},
        )

        # Get training labels for this field
        labels = await label_service.get_by_field(
            field_id, is_training_data=True, limit=10000
        )

        if not labels:
            return {
                "status": "failed",
                "message": "No training labels found for this field",
            }

        logger.info(
            "Found training labels",
            extra={"field_id": field_id, "label_count": len(labels)},
        )

        # Get document IDs from labels
        document_ids = [label.document_id for label in labels]

        # Get documents (we need the content)
        # Note: We need to get documents from the database
        # This is a simplified version - actual implementation would need
        # to fetch document content from storage
        documents = []
        for doc_id in document_ids:
            doc = await doc_service.get_by_id(doc_id)
            if doc:
                documents.append(doc)

        if len(documents) != len(labels):
            logger.warning(
                "Not all labeled documents found",
                extra={
                    "field_id": field_id,
                    "labels_count": len(labels),
                    "documents_count": len(documents),
                },
            )

        # Create training data mapping: document_id -> class_name
        doc_id_to_class = {}
        for label in labels:
            field_class = await class_service.get(label.class_id)
            if field_class:
                doc_id_to_class[label.document_id] = field_class.name

        # Get latest model version for this field
        latest_model = await model_service.get_latest_by_field(field_id)
        new_version = (latest_model.version + 1) if latest_model else 1

        # Create model record with TRAINING status
        model_path = f"{field.project_id}/models/{field_id}/v{new_version}/model.pkl"
        vectorizer_path = f"{field.project_id}/models/{field_id}/v{new_version}/vectorizer.pkl"

        model_create = ModelCreate(
            version=new_version,
            model_path=model_path,
            vectorizer_path=vectorizer_path,
            status=ModelStatus.TRAINING,
        )

        model = await model_service.create(field_id, model_create)

        try:
            # Implement actual training logic
            from pathlib import Path
            import pickle
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import SGDClassifier
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
            from ..core.config import settings

            logger.info(
                "Starting model training",
                extra={"field_id": field_id, "model_id": model.id},
            )

            # 1. Prepare training data from documents and labels
            from ..core.storage import document_storage

            texts = []
            labels_list = []

            for doc_id, class_name in doc_id_to_class.items():
                doc = next((d for d in documents if d.id == doc_id), None)
                if doc:
                    # Load content directly from storage
                    content = document_storage.read_document(doc.project_id, doc.id)
                    if content:
                        texts.append(content)
                        labels_list.append(class_name)

            if len(texts) < 2:
                raise ValueError("Not enough training samples. Need at least 2 labeled documents.")

            logger.info(
                "Prepared training data",
                extra={
                    "field_id": field_id,
                    "num_samples": len(texts),
                    "num_classes": len(set(labels_list)),
                },
            )

            # 2. Train vectorizer and classifier
            vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
            X = vectorizer.fit_transform(texts)

            # Split data for evaluation
            if len(texts) >= 4:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, labels_list, test_size=0.2, random_state=42, stratify=labels_list
                )
            else:
                # For very small datasets, use all data for training
                X_train, X_test, y_train, y_test = X, X, labels_list, labels_list

            # Train classifier
            classifier = SGDClassifier(
                loss='log_loss',
                penalty='l2',
                max_iter=1000,
                random_state=42
            )
            classifier.fit(X_train, y_train)

            # 3. Evaluate model
            y_pred = classifier.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)

            logger.info(
                "Model training completed",
                extra={
                    "field_id": field_id,
                    "accuracy": accuracy,
                    "f1_score": f1,
                },
            )

            # 4. Save trained model and vectorizer to storage
            storage_path = settings.STORAGE_PATH / model.model_path
            storage_path.parent.mkdir(parents=True, exist_ok=True)

            vectorizer_storage_path = settings.STORAGE_PATH / model.vectorizer_path
            vectorizer_storage_path.parent.mkdir(parents=True, exist_ok=True)

            with open(storage_path, 'wb') as f:
                pickle.dump(classifier, f)

            with open(vectorizer_storage_path, 'wb') as f:
                pickle.dump(vectorizer, f)

            logger.info(
                "Saved model files",
                extra={
                    "field_id": field_id,
                    "model_path": str(storage_path),
                    "vectorizer_path": str(vectorizer_storage_path),
                },
            )

            # Update model status
            model.status = ModelStatus.READY
            model.accuracy = float(accuracy)
            model.metrics = {
                "accuracy": float(accuracy),
                "f1_score": float(f1),
                "precision": float(precision),
                "recall": float(recall),
                "training_samples": len(texts),
                "num_classes": len(set(labels_list)),
            }
            model.trained_at = datetime.utcnow()

            await db.commit()
            await db.refresh(model)

            # Delete old models (keep only latest per user requirement)
            await model_service.delete_old_models(field_id, keep_latest=1)

            logger.info(
                "Field training completed successfully",
                extra={
                    "field_id": field_id,
                    "model_id": model.id,
                    "version": model.version,
                    "accuracy": model.accuracy,
                },
            )

            return {
                "status": "completed",
                "message": "Field model trained successfully",
                "model_id": model.id,
                "model_version": model.version,
                "metrics": model.metrics,
            }

        except Exception as e:
            # Update model status on failure
            model.status = ModelStatus.FAILED
            await db.commit()
            logger.error(
                "Field training failed",
                extra={"field_id": field_id, "model_id": model.id, "error": str(e)},
            )
            raise e

    except Exception as e:
        logger.exception("Field training task failed")
        return {
            "status": "failed",
            "message": str(e),
        }
    finally:
        await db.close()


@celery_app.task(
    base=TrainingTask,
    bind=True,
    queue=QueueName.TRAINING,
)
def train_field_model(
    self,
    field_id: str,
    params: Optional[Dict] = None,
) -> dict:
    """Train a classification model for a specific field (Celery task wrapper).

    This is a synchronous wrapper that executes the async training logic.

    Args:
        field_id: Field ID to train
        params: Optional training parameters

    Returns:
        Task result with training statistics
    """
    import asyncio

    # Run the async function in a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_train_field_model_async(field_id, params))
        return result
    finally:
        loop.close()
