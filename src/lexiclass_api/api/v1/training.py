"""Training API endpoints."""

from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.deps import get_db
from ...core.worker import worker
from ...services.projects import ProjectService

router = APIRouter()


class TrainingParams(BaseModel):
    """Training parameters."""

    params: Optional[Dict] = None


@router.post(
    "/{project_id}/train",
    tags=["training"],
)
async def trigger_training(
    *,
    project_id: str,
    params: Optional[TrainingParams] = None,
    db: AsyncSession = Depends(get_db),

) -> dict:
    """Trigger model training.

    Args:
        project_id: Project ID
        params: Optional training parameters
        db: Database session


    Returns:
        Task information

    Raises:
        HTTPException: If project not found or invalid state
    """
    # Verify project exists
    service = ProjectService(db)
    project = await service.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check if training is already in progress
    if project.model_status == "training":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Training already in progress",
        )

    # TODO: This endpoint needs to be updated to use field-based training
    # The new architecture requires training individual fields, not projects
    # Use the field training endpoint instead: POST /fields/{field_id}/train
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Project-level training is deprecated. Please use field-based training endpoints: POST /fields/{field_id}/train",
    )


@router.get(
    "/{project_id}/train/status",
    tags=["training"],
)
async def get_training_status(
    *,
    project_id: str,
    db: AsyncSession = Depends(get_db),

) -> dict:
    """Get training status.

    Args:
        project_id: Project ID
        db: Database session


    Returns:
        Training status information

    Raises:
        HTTPException: If project not found
    """
    # Verify project exists
    service = ProjectService(db)
    project = await service.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return {
        "status": project.model_status or "not_started",
        "version": project.model_version,
        "metrics": project.model_metrics,
        "last_trained": project.model_updated_at,
    }
