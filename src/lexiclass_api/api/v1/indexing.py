"""Indexing API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.deps import get_db
from ...core.worker import worker, TaskResult
from ...core.config import settings
from ...models import IndexStatus, ProjectIndexStatus
from ...services.documents import DocumentService
from ...services.projects import ProjectService

router = APIRouter()


@router.post(
    "/{project_id}/index",
    tags=["indexing"],
)
async def trigger_indexing(
    *,
    project_id: int,
    is_incremental: bool = True,
    db: AsyncSession = Depends(get_db),

) -> dict:
    """Trigger document indexing.

    Args:
        project_id: Project ID
        is_incremental: Whether to perform incremental indexing
        db: Database session


    Returns:
        Task information

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

    # Update project index_status to IN_PROGRESS
    project.index_status = ProjectIndexStatus.IN_PROGRESS

    # Update all documents index_status to pending
    doc_service = DocumentService(db)
    docs = await doc_service.get_multi(project_id)
    for doc in docs:
        doc.index_status = IndexStatus.PENDING
    await db.commit()

    # Construct storage path
    documents_path = str(settings.get_documents_path(project_id).resolve())

    # Submit task to worker
    task = worker.index_documents(
        project_id=project_id,
        documents_path=documents_path,
        is_incremental=is_incremental,
    )

    return {
        "task_id": task.id,
        "status": "pending",
        "message": "Indexing task submitted to worker",
    }


@router.get(
    "/{project_id}/index/status",
    tags=["indexing"],
)
async def get_index_status(
    *,
    project_id: int,
    db: AsyncSession = Depends(get_db),

) -> dict:
    """Get indexing status for a project.

    Args:
        project_id: Project ID
        db: Database session


    Returns:
        Index status information

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

    # Get document statistics
    doc_service = DocumentService(db)
    total = await doc_service.count(project_id)
    indexed = await doc_service.count(project_id, index_status=IndexStatus.INDEXED)
    pending = await doc_service.count(project_id, index_status=IndexStatus.PENDING)
    failed = await doc_service.count(project_id, index_status=IndexStatus.FAILED)

    # Determine overall status
    if project.index_status:
        overall_status = project.index_status.value
    else:
        overall_status = "not_started"

    return {
        "status": overall_status,
        "project_index_status": project.index_status.value if project.index_status else None,
        "last_indexed_at": project.last_indexed_at.isoformat() if project.last_indexed_at else None,
        "total_documents": total,
        "indexed_documents": indexed,
        "pending_documents": pending,
        "failed_documents": failed,
    }


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResult,
    tags=["indexing"],
)
async def get_task_status(
    task_id: str,

) -> TaskResult:
    """Get status of a specific task.

    Args:
        task_id: Task ID


    Returns:
        Task status information
    """
    return worker.get_task_status(task_id)