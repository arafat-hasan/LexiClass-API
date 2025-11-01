"""Training API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.deps import get_db
from ...services.projects import ProjectService

router = APIRouter()


@router.get(
    "/{project_id}/train/status",
    tags=["training"],
)
async def get_training_status(
    *,
    project_id: int,
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
