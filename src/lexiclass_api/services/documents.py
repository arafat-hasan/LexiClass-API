"""Document service."""

from typing import List, Optional, Sequence
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.document import Document as DocumentModel
from ..schemas.document import DocumentBulkCreate, Document


class DocumentService:
    """Document service."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service.

        Args:
            db: Database session
        """
        self.db = db

    async def _check_existing_ids(self, document_ids: List[str]) -> None:
        """Check if any of the document IDs already exist.

        Args:
            document_ids: List of document IDs to check

        Raises:
            HTTPException: If any of the document IDs already exist
        """
        if not document_ids:
            return

        query = select(DocumentModel.id).where(DocumentModel.id.in_(document_ids))
        result = await self.db.execute(query)
        existing_ids = result.scalars().all()

        if existing_ids:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Documents with IDs {existing_ids} already exist",
            )

    async def create_bulk(
        self, project_id: str, documents_in: DocumentBulkCreate
    ) -> List[Document]:
        """Create multiple documents.

        Args:
            project_id: Project ID
            documents_in: Documents to create

        Returns:
            Created documents
        """
        # Check for existing IDs
        existing_ids = [doc.id for doc in documents_in.documents if doc.id is not None]
        await self._check_existing_ids(existing_ids)

        # Create document models
        db_documents = [
            DocumentModel(
                project_id=project_id,
                id=doc.id or str(uuid.uuid4()),  # Use provided ID or generate UUID
                content=doc.content,
                metadata=doc.metadata,
                label=doc.label,
                status="pending",
            )
            for doc in documents_in.documents
        ]

        # Add to DB
        self.db.add_all(db_documents)
        await self.db.commit()

        # Refresh to get generated values
        for doc in db_documents:
            await self.db.refresh(doc)

        return [Document.model_validate(doc) for doc in db_documents]

    async def get_multi(
        self,
        project_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
        label: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Sequence[Document]:
        """Get multiple documents.

        Args:
            project_id: Project ID
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            label: Filter by label
            status: Filter by status

        Returns:
            List of documents
        """
        # Build query
        query = select(DocumentModel).where(DocumentModel.project_id == project_id)

        # Apply filters
        if label is not None:
            query = query.where(DocumentModel.label == label)
        if status is not None:
            query = query.where(DocumentModel.status == status)

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        documents = result.scalars().all()

        return [Document.model_validate(doc) for doc in documents]

    async def delete_multi(self, project_id: str, document_ids: List[str]) -> None:
        """Delete multiple documents.

        Args:
            project_id: Project ID
            document_ids: IDs of documents to delete
        """
        # Delete documents
        query = (
            select(DocumentModel)
            .where(DocumentModel.project_id == project_id)
            .where(DocumentModel.id.in_(document_ids))
        )
        result = await self.db.execute(query)
        documents = result.scalars().all()

        for doc in documents:
            await self.db.delete(doc)

        await self.db.commit()
