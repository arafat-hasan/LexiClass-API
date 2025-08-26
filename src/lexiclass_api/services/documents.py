"""Document service."""

from typing import List, Optional, Sequence
import uuid

# Service constants
MAX_PAGE_SIZE = 1000  # Maximum number of documents per page
DEFAULT_PAGE_SIZE = 100  # Default number of documents per page
MAX_BATCH_SIZE = 500  # Maximum number of documents in a bulk create operation

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

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

        Returns:
            None

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
            documents_in: Documents to create (maximum 500 documents per batch)

        Returns:
            Created documents

        Raises:
            HTTPException: If there's a conflict with existing IDs, batch size exceeds limit,
                         or database error occurs
        """
        # Validate batch size
        if not documents_in.documents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No documents provided for creation"
            )

        if len(documents_in.documents) > MAX_BATCH_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch size exceeds maximum limit of {MAX_BATCH_SIZE} documents"
            )

        try:
            # Check for existing IDs
            existing_ids = [doc.id for doc in documents_in.documents if doc.id is not None]
            await self._check_existing_ids(existing_ids)

            # Create document models
            db_documents = [
                DocumentModel(
                    project_id=project_id,
                    id=doc.id or str(uuid.uuid4()),  # Use provided ID or generate UUID
                    content_path="",  # Will be set by the model after insert
                    _content=doc.content,  # This will trigger content storage
                    doc_metadata=doc.metadata,  # Note: using doc_metadata to match model field name
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

            return [self._convert_to_pydantic(doc) for doc in db_documents]
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error while creating documents: {str(e)}"
            ) from e

    async def get_multi(
        self,
        project_id: str,
        *,
        skip: int = 0,
        limit: int = DEFAULT_PAGE_SIZE,
        label: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Sequence[Document]:
        """Get multiple documents.

        Args:
            project_id: Project ID
            skip: Number of documents to skip (must be >= 0)
            limit: Maximum number of documents to return (1-1000)
            label: Filter by label
            status: Filter by status

        Returns:
            List of documents

        Raises:
            HTTPException: If pagination parameters are invalid
        """
        # Validate pagination parameters
        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skip parameter must be non-negative"
            )

        if limit < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit parameter must be greater than 0"
            )

        if limit > MAX_PAGE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Limit parameter cannot exceed {MAX_PAGE_SIZE}"
            )

        try:
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

            return [self._convert_to_pydantic(doc) for doc in documents]
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error while fetching documents: {str(e)}"
            ) from e

    def _convert_to_pydantic(self, doc: DocumentModel) -> Document:
        """Convert SQLAlchemy model to Pydantic model.

        Args:
            doc: SQLAlchemy document model

        Returns:
            Pydantic document model
        """
        return Document.model_validate({
            **{k: v for k, v in doc.__dict__.items() if not k.startswith('_')},
            'metadata': doc.doc_metadata  # Map doc_metadata to metadata for Pydantic
        })

    async def get_multi_by_ids(self, project_id: str, document_ids: List[str]) -> Sequence[Document]:
        """Get multiple documents by their IDs.

        Args:
            project_id: Project ID
            document_ids: List of document IDs to retrieve

        Returns:
            List of documents
        """
        query = (
            select(DocumentModel)
            .where(DocumentModel.project_id == project_id)
            .where(DocumentModel.id.in_(document_ids))
        )
        result = await self.db.execute(query)
        documents = result.scalars().all()

        return [self._convert_to_pydantic(doc) for doc in documents]

    async def delete_multi(self, project_id: str, document_ids: List[str]) -> None:
        """Delete multiple documents.

        Args:
            project_id: Project ID
            document_ids: IDs of documents to delete

        Returns:
            None

        Raises:
            HTTPException: If there's a database error during deletion
        """
        try:
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
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error while deleting documents: {str(e)}"
            ) from e
