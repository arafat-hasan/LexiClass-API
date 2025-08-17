"""Prediction API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.deps import get_current_user, get_db
from ...models.user import User
from ...schemas.document import Document
from ...services.documents import DocumentService
from ...services.projects import ProjectService
from ...tasks.prediction import predict_documents

router = APIRouter()


@router.post(
    "/{project_id}/predict",
    tags=["prediction"],
)
async def trigger_prediction(
    *,
    project_id: str,
    document_ids: Optional[List[str]] = Query(None, max_items=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Trigger document prediction.

    Args:
        project_id: Project ID
        document_ids: Optional list of document IDs to predict
        db: Database session
        current_user: Current user

    Returns:
        Task information

    Raises:
        HTTPException: If project not found or invalid state
    """
    # Verify project exists and has trained model
    project_service = ProjectService(db)
    project = await project_service.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    if project.model_status != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model not ready for predictions",
        )

    # Verify documents exist if specific IDs provided
    if document_ids:
        doc_service = DocumentService(db)
        docs = await doc_service.get_multi_by_ids(project_id, document_ids)
        if len(docs) != len(document_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more documents not found",
            )

    # Trigger prediction task
    task = predict_documents.delay(
        project_id=project_id,
        document_ids=document_ids,
    )

    return {
        "task_id": task.id,
        "status": "pending",
        "message": "Prediction task started",
    }


@router.get(
    "/{project_id}/predict/{prediction_id}",
    response_model=List[Document],
    tags=["prediction"],
)
async def get_prediction_results(
    *,
    project_id: str,
    prediction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> List[Document]:
    """Get prediction results.

    Args:
        project_id: Project ID
        prediction_id: Prediction ID
        db: Database session
        current_user: Current user
        skip: Number of documents to skip
        limit: Maximum number of documents to return

    Returns:
        List of documents with predictions

    Raises:
        HTTPException: If project or prediction not found
    """
    # Verify project exists
    project_service = ProjectService(db)
    project = await project_service.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Get documents with predictions
    doc_service = DocumentService(db)
    documents = await doc_service.get_multi(
        project_id=project_id,
        prediction_id=prediction_id,
        skip=skip,
        limit=limit,
    )

    if not documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No predictions found",
        )

    return list(documents)


@router.get(
    "/{project_id}/predict/latest",
    response_model=List[Document],
    tags=["prediction"],
)
async def get_latest_predictions(
    *,
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> List[Document]:
    """Get latest prediction results.

    Args:
        project_id: Project ID
        db: Database session
        current_user: Current user
        skip: Number of documents to skip
        limit: Maximum number of documents to return

    Returns:
        List of documents with latest predictions

    Raises:
        HTTPException: If project not found
    """
    # Verify project exists
    project_service = ProjectService(db)
    project = await project_service.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Get documents with latest predictions
    doc_service = DocumentService(db)
    documents = await doc_service.get_multi(
        project_id=project_id,
        has_prediction=True,  # Only get documents with predictions
        skip=skip,
        limit=limit,
        order_by="-updated_at",  # Order by most recent predictions
    )

    if not documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No predictions found",
        )

    return list(documents)
