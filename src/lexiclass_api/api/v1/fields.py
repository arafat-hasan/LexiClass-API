"""Field API endpoints."""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.deps import get_db
from ...models import ModelStatus
from ...schemas.document_label import DocumentLabel, DocumentLabelCreate, DocumentLabelUpdate
from ...schemas.field import Field, FieldCreate, FieldUpdate
from ...schemas.field_class import FieldClass, FieldClassCreate, FieldClassUpdate
from ...schemas.prediction import Prediction
from ...services.document_labels import DocumentLabelService
from ...services.documents import DocumentService
from ...services.field_classes import FieldClassService
from ...services.fields import FieldService
from ...services.predictions import PredictionService
from ...services.projects import ProjectService

router = APIRouter()


# Field Management Endpoints

@router.post(
    "/projects/{project_id}/fields",
    response_model=Field,
    status_code=status.HTTP_201_CREATED,
    tags=["fields"],
)
async def create_field(
    *,
    project_id: str,
    field_in: FieldCreate,
    db: AsyncSession = Depends(get_db),
) -> Field:
    """Create new field for a project."""
    # Verify project exists
    project_service = ProjectService(db)
    project = await project_service.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    service = FieldService(db)
    field = await service.create(project_id, field_in)
    return field


@router.get("/fields/{field_id}", response_model=Field, tags=["fields"])
async def get_field(
    field_id: str,
    db: AsyncSession = Depends(get_db),
) -> Field:
    """Get field by ID."""
    service = FieldService(db)
    field = await service.get(field_id)
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found",
        )
    return field


@router.get(
    "/projects/{project_id}/fields", response_model=List[Field], tags=["fields"]
)
async def list_project_fields(
    *,
    project_id: str,
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> List[Field]:
    """List fields for a project."""
    # Verify project exists
    project_service = ProjectService(db)
    project = await project_service.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    service = FieldService(db)
    fields = await service.get_by_project(project_id, skip=skip, limit=limit)
    return list(fields)


@router.put("/fields/{field_id}", response_model=Field, tags=["fields"])
async def update_field(
    *,
    field_id: str,
    field_in: FieldUpdate,
    db: AsyncSession = Depends(get_db),
) -> Field:
    """Update field."""
    service = FieldService(db)
    field = await service.get(field_id)
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found",
        )
    field = await service.update(field, field_in)
    return field


@router.delete(
    "/fields/{field_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["fields"]
)
async def delete_field(
    *,
    field_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete field."""
    service = FieldService(db)
    field = await service.get(field_id)
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found",
        )
    await service.delete(field)


# Field Class Management Endpoints

@router.post(
    "/fields/{field_id}/classes",
    response_model=FieldClass,
    status_code=status.HTTP_201_CREATED,
    tags=["field-classes"],
)
async def create_field_class(
    *,
    field_id: str,
    class_in: FieldClassCreate,
    db: AsyncSession = Depends(get_db),
) -> FieldClass:
    """Create new class for a field."""
    # Verify field exists
    field_service = FieldService(db)
    field = await field_service.get(field_id)
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found",
        )

    service = FieldClassService(db)
    field_class = await service.create(field_id, class_in)
    return field_class


@router.get(
    "/classes/{class_id}", response_model=FieldClass, tags=["field-classes"]
)
async def get_field_class(
    class_id: str,
    db: AsyncSession = Depends(get_db),
) -> FieldClass:
    """Get field class by ID."""
    service = FieldClassService(db)
    field_class = await service.get(class_id)
    if not field_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field class not found",
        )
    return field_class


@router.get(
    "/fields/{field_id}/classes",
    response_model=List[FieldClass],
    tags=["field-classes"],
)
async def list_field_classes(
    *,
    field_id: str,
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> List[FieldClass]:
    """List classes for a field."""
    # Verify field exists
    field_service = FieldService(db)
    field = await field_service.get(field_id)
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found",
        )

    service = FieldClassService(db)
    classes = await service.get_by_field(field_id, skip=skip, limit=limit)
    return list(classes)


@router.put(
    "/classes/{class_id}", response_model=FieldClass, tags=["field-classes"]
)
async def update_field_class(
    *,
    class_id: str,
    class_in: FieldClassUpdate,
    db: AsyncSession = Depends(get_db),
) -> FieldClass:
    """Update field class."""
    service = FieldClassService(db)
    field_class = await service.get(class_id)
    if not field_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field class not found",
        )
    field_class = await service.update(field_class, class_in)
    return field_class


@router.delete(
    "/classes/{class_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["field-classes"],
)
async def delete_field_class(
    *,
    class_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete field class."""
    service = FieldClassService(db)
    field_class = await service.get(class_id)
    if not field_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field class not found",
        )
    await service.delete(field_class)


# Document Label Management Endpoints

@router.post(
    "/documents/{document_id}/labels",
    response_model=DocumentLabel,
    status_code=status.HTTP_201_CREATED,
    tags=["document-labels"],
)
async def create_document_label(
    *,
    document_id: str,
    label_in: DocumentLabelCreate,
    db: AsyncSession = Depends(get_db),
) -> DocumentLabel:
    """Assign label to document for a field.

    If a label already exists for this document and field, it will be updated.
    """
    # Verify document exists
    document_service = DocumentService(db)
    document = await document_service.get_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Verify field exists
    field_service = FieldService(db)
    field = await field_service.get(label_in.field_id)
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found",
        )

    # Verify class exists and belongs to the field
    class_service = FieldClassService(db)
    field_class = await class_service.get(label_in.class_id)
    if not field_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field class not found",
        )
    if field_class.field_id != label_in.field_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field class does not belong to the specified field",
        )

    service = DocumentLabelService(db)
    label = await service.create(document_id, label_in)
    return label


@router.get("/labels/{label_id}", response_model=DocumentLabel, tags=["document-labels"])
async def get_document_label(
    label_id: str,
    db: AsyncSession = Depends(get_db),
) -> DocumentLabel:
    """Get document label by ID."""
    service = DocumentLabelService(db)
    label = await service.get(label_id)
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document label not found",
        )
    return label


@router.get(
    "/documents/{document_id}/labels",
    response_model=List[DocumentLabel],
    tags=["document-labels"],
)
async def list_document_labels(
    *,
    document_id: str,
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> List[DocumentLabel]:
    """Get all labels for a document."""
    # Verify document exists
    document_service = DocumentService(db)
    document = await document_service.get_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    service = DocumentLabelService(db)
    labels = await service.get_by_document(document_id, skip=skip, limit=limit)
    return list(labels)


@router.get(
    "/documents/{document_id}/labels/{field_id}",
    response_model=DocumentLabel,
    tags=["document-labels"],
)
async def get_document_label_by_field(
    *,
    document_id: str,
    field_id: str,
    db: AsyncSession = Depends(get_db),
) -> DocumentLabel:
    """Get label for a specific document and field."""
    service = DocumentLabelService(db)
    label = await service.get_by_document_and_field(document_id, field_id)
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Label not found for this document and field",
        )
    return label


@router.put("/labels/{label_id}", response_model=DocumentLabel, tags=["document-labels"])
async def update_document_label(
    *,
    label_id: str,
    label_in: DocumentLabelUpdate,
    db: AsyncSession = Depends(get_db),
) -> DocumentLabel:
    """Update document label."""
    service = DocumentLabelService(db)
    label = await service.get(label_id)
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document label not found",
        )

    # Verify new class exists and belongs to the same field
    class_service = FieldClassService(db)
    field_class = await class_service.get(label_in.class_id)
    if not field_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field class not found",
        )
    if field_class.field_id != label.field_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change label to a class from a different field",
        )

    label = await service.update(label, label_in)
    return label


@router.delete(
    "/labels/{label_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["document-labels"],
)
async def delete_document_label(
    *,
    label_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete document label."""
    service = DocumentLabelService(db)
    label = await service.get(label_id)
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document label not found",
        )
    await service.delete(label)


# Field Training Endpoints

class FieldTrainingParams(BaseModel):
    """Field training parameters."""

    params: Optional[Dict] = None


@router.post(
    "/fields/{field_id}/train",
    tags=["training"],
)
async def train_field(
    *,
    field_id: str,
    params: Optional[FieldTrainingParams] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Trigger model training for a field.

    Trains a classification model for the specified field using labeled documents.
    Only documents with is_training_data=True will be used for training.

    Args:
        field_id: Field ID to train
        params: Optional training parameters
        db: Database session

    Returns:
        Task information

    Raises:
        HTTPException: If field not found or training already in progress
    """
    from ...core.worker import worker

    # Verify field exists
    field_service = FieldService(db)
    field = await field_service.get(field_id)
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found",
        )

    # Check if there are any training labels for this field
    label_service = DocumentLabelService(db)
    labels = await label_service.get_by_field(field_id, is_training_data=True, limit=1)
    if not labels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No training labels found for this field",
        )

    # Submit field training task to worker
    task = worker.train_field_model(
        field_id=field_id,
        project_id=field.project_id,
    )

    return {
        "task_id": task.id,
        "status": "pending",
        "message": "Field training task started",
    }


# Field Prediction Endpoints

class FieldPredictionParams(BaseModel):
    """Field prediction parameters."""

    document_ids: List[str]
    params: Optional[Dict] = None


@router.post(
    "/fields/{field_id}/predict",
    tags=["prediction"],
)
async def predict_for_field(
    *,
    field_id: str,
    prediction_params: FieldPredictionParams,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Trigger predictions for documents using a field's model.

    Makes predictions for the specified documents using the latest ready model
    for this field. Predictions are stored in the Prediction table.

    Args:
        field_id: Field ID to use for prediction
        prediction_params: Document IDs and optional parameters
        db: Database session

    Returns:
        Task information

    Raises:
        HTTPException: If field not found or no ready model available
    """
    from ...core.worker import worker

    # Verify field exists
    field_service = FieldService(db)
    field = await field_service.get(field_id)
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found",
        )

    # Check if there's a ready model for this field
    from ...services.models import ModelService
    model_service = ModelService(db)
    model = await model_service.get_latest_ready_by_field(field_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No ready model found for this field. Please train the model first.",
        )

    # Verify documents exist
    doc_service = DocumentService(db)
    # Check each document exists
    for doc_id in prediction_params.document_ids:
        doc = await doc_service.get_by_id(doc_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found",
            )

    # Submit field prediction task to worker
    task = worker.predict_field_documents(
        field_id=field_id,
        project_id=field.project_id,
        document_ids=prediction_params.document_ids,
    )

    return {
        "task_id": task.id,
        "status": "pending",
        "message": "Field prediction task started",
        "document_count": len(prediction_params.document_ids),
    }


@router.get(
    "/documents/{document_id}/predictions",
    response_model=List[Prediction],
    tags=["prediction"],
)
async def get_document_predictions(
    *,
    document_id: str,
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> List[Prediction]:
    """Get all predictions for a document across all fields."""
    # Verify document exists
    doc_service = DocumentService(db)
    documents = await doc_service.get_multi_by_ids("", [document_id])
    if not documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    prediction_service = PredictionService(db)
    predictions = await prediction_service.get_by_document(
        document_id, skip=skip, limit=limit
    )
    return list(predictions)


@router.get(
    "/documents/{document_id}/predictions/{field_id}",
    response_model=Prediction,
    tags=["prediction"],
)
async def get_document_prediction_by_field(
    *,
    document_id: str,
    field_id: str,
    db: AsyncSession = Depends(get_db),
) -> Prediction:
    """Get prediction for a specific document and field."""
    prediction_service = PredictionService(db)
    prediction = await prediction_service.get_by_document_and_field(
        document_id, field_id
    )
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found for this document and field",
        )
    return prediction
