"""Document API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.deps import get_current_user, get_db
from ...models.user import User
from ...schemas.document import Document, DocumentBulkCreate
from ...services.documents import DocumentService
from ...services.projects import ProjectService

router = APIRouter()


@router.post(
    "/{project_id}/documents",
    response_model=List[Document],
    status_code=status.HTTP_201_CREATED,
    tags=["documents"],
)
async def create_documents(
    *,
    project_id: str,
    documents_in: DocumentBulkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Document]:
    """Create new documents in a project.

    Args:
        project_id: Project ID
        documents_in: Documents to create
        db: Database session
        current_user: Current user

    Returns:
        Created documents

    Raises:
        HTTPException: If project not found or validation error
    """
    # Verify project exists
    project_service = ProjectService(db)
    project = await project_service.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Create documents
    service = DocumentService(db)
    documents = await service.create_bulk(project_id, documents_in)
    return documents


@router.get(
    "/{project_id}/documents",
    response_model=List[Document],
    tags=["documents"],
)
async def list_documents(
    *,
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    label: str | None = None,
    status: str | None = None,
) -> List[Document]:
    """List documents in a project.

    Args:
        project_id: Project ID
        db: Database session
        current_user: Current user
        skip: Number of documents to skip
        limit: Maximum number of documents to return
        label: Filter by label
        status: Filter by status

    Returns:
        List of documents

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

    # Get documents
    service = DocumentService(db)
    documents = await service.get_multi(
        project_id=project_id,
        skip=skip,
        limit=limit,
        label=label,
        status=status,
    )
    return list(documents)


@router.delete(
    "/{project_id}/documents",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["documents"],
)
async def delete_documents(
    *,
    project_id: str,
    document_ids: List[str] = Query(..., min_items=1, max_items=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete documents from a project.

    Args:
        project_id: Project ID
        document_ids: IDs of documents to delete
        db: Database session
        current_user: Current user

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

    # Delete documents
    service = DocumentService(db)
    await service.delete_multi(project_id, document_ids)
