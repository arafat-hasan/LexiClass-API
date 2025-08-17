"""Indexing API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.deps import get_current_user, get_db
from ...core.worker import worker
from ...models.user import User
from ...services.documents import DocumentService
from ...services.projects import ProjectService

router = APIRouter()


@router.post(
    "/{project_id}/index",
    tags=["indexing"],
)
async def trigger_indexing(
    *,
    project_id: str,
    document_ids: Optional[List[str]] = Query(None, max_items=1000),
    is_incremental: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Trigger document indexing.

    Args:
        project_id: Project ID
        document_ids: Optional list of document IDs to index
        is_incremental: Whether to perform incremental indexing
        db: Database session
        current_user: Current user

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

    # Verify documents exist if specific IDs provided
    if document_ids:
        doc_service = DocumentService(db)
        docs = await doc_service.get_multi_by_ids(project_id, document_ids)
        if len(docs) != len(document_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more documents not found",
            )

        # Update document status to pending
        for doc in docs:
            doc.status = "pending"
        await db.commit()

    # Submit task to worker
    task = worker.index_documents(
        project_id=project_id,
        document_ids=document_ids,
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
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get indexing status for a project.

    Args:
        project_id: Project ID
        db: Database session
        current_user: Current user

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
    indexed = await doc_service.count(project_id, status="indexed")
    pending = await doc_service.count(project_id, status="pending")
    failed = await doc_service.count(project_id, status="failed")

    return {
        "status": "valid" if indexed > 0 else "missing",
        "total_documents": total,
        "indexed_documents": indexed,
        "pending_documents": pending,
        "failed_documents": failed,
    }


@router.get(
    "/tasks/{task_id}",
    tags=["indexing"],
)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get status of a specific task.

    Args:
        task_id: Task ID
        current_user: Current user

    Returns:
        Task status information
    """
    return worker.get_task_status(task_id)