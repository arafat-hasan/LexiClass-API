"""Document service."""

from typing import List, Optional, Sequence

# Service constants
MAX_PAGE_SIZE = 1000  # Maximum number of documents per page
DEFAULT_PAGE_SIZE = 100  # Default number of documents per page
MAX_BATCH_SIZE = 500  # Maximum number of documents in a bulk create operation

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from ..models import Document as DocumentModel, IndexStatus
from ..schemas import (
    DocumentBulkCreate,
    Document,
    DocumentBulkDelete,
    DocumentBulkDeleteResponse,
    DocumentDeletionResult,
)


class DocumentService:
    """Document service."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service.

        Args:
            db: Database session
        """
        self.db = db

    async def _check_existing_ids(self, document_ids: List[int]) -> None:
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
        self, project_id: int, documents_in: DocumentBulkCreate
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

            # Store content files FIRST and get paths
            from ..core.storage import document_storage

            # Create document models with content already stored
            db_documents = []
            docs_with_id = []  # Documents with provided IDs

            for doc in documents_in.documents:
                # For new documents without ID, we need to create the record first to get auto-generated ID
                # Then store content using that ID
                if doc.id is not None:
                    # ID provided, use it directly
                    doc_id = doc.id
                    path = document_storage.store_document(project_id, doc_id, doc.content)

                    db_doc = DocumentModel(
                        project_id=project_id,
                        id=doc_id,
                        content_path=str(path),
                        doc_metadata=doc.metadata,
                        index_status=IndexStatus.PENDING,
                    )
                    docs_with_id.append(db_doc)
                    db_documents.append(db_doc)
                else:
                    # No ID provided, create record first to get auto-generated ID
                    # Store with temporary path, then update after getting ID
                    db_doc = DocumentModel(
                        project_id=project_id,
                        content_path="",  # Temporary, will be updated
                        doc_metadata=doc.metadata,
                        index_status=IndexStatus.PENDING,
                    )
                    self.db.add(db_doc)
                    await self.db.flush()  # Get the auto-generated ID

                    # Now store content with actual ID
                    path = document_storage.store_document(project_id, db_doc.id, doc.content)
                    db_doc.content_path = str(path)
                    db_documents.append(db_doc)

            # Add documents with provided IDs (documents without ID are already in session)
            if docs_with_id:
                self.db.add_all(docs_with_id)

            await self.db.commit()

            # Don't refresh - we already have all the data we need
            # Convert to Pydantic without accessing lazy-loaded relationships
            return [self._convert_to_pydantic_simple(doc) for doc in db_documents]
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error while creating documents: {str(e)}"
            ) from e

    async def get_multi(
        self,
        project_id: int,
        *,
        skip: int = 0,
        limit: int = DEFAULT_PAGE_SIZE,
        label: Optional[str] = None,
        index_status: Optional[IndexStatus] = None,
    ) -> Sequence[Document]:
        """Get multiple documents.

        Args:
            project_id: Project ID
            skip: Number of documents to skip (must be >= 0)
            limit: Maximum number of documents to return (1-1000)
            label: Filter by label
            index_status: Filter by index status

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
            if index_status is not None:
                query = query.where(DocumentModel.index_status == index_status)

            # Apply pagination
            query = query.offset(skip).limit(limit)

            # Execute query
            result = await self.db.execute(query)
            documents = result.scalars().all()

            return [self._convert_to_pydantic_simple(doc) for doc in documents]
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error while fetching documents: {str(e)}"
            ) from e

    async def count(
        self,
        project_id: int,
        *,
        label: Optional[str] = None,
        index_status: Optional[IndexStatus] = None,
    ) -> int:
        """Count documents matching the given criteria.

        Args:
            project_id: Project ID
            label: Filter by label
            index_status: Filter by index status

        Returns:
            Number of documents matching the criteria

        Raises:
            HTTPException: If there's a database error
        """
        try:
            # Build query
            query = select(func.count(DocumentModel.id)).where(
                DocumentModel.project_id == project_id
            )

            # Apply filters
            if label is not None:
                query = query.where(DocumentModel.label == label)
            if index_status is not None:
                query = query.where(DocumentModel.index_status == index_status)

            # Execute query
            result = await self.db.execute(query)
            count = result.scalar()

            return count or 0
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error while counting documents: {str(e)}"
            ) from e

    async def get_by_id(self, document_id: int) -> Optional[Document]:
        """Get document by ID.

        Args:
            document_id: Document ID

        Returns:
            Document if found, None otherwise
        """
        query = select(DocumentModel).where(DocumentModel.id == document_id)
        result = await self.db.execute(query)
        doc = result.scalar_one_or_none()

        if doc:
            return self._convert_to_pydantic_simple(doc)
        return None

    def _convert_to_pydantic_simple(self, doc: DocumentModel) -> Document:
        """Convert SQLAlchemy model to Pydantic model without accessing relationships.

        Args:
            doc: SQLAlchemy document model

        Returns:
            Pydantic document model
        """
        return Document.model_validate({
            'id': doc.id,
            'project_id': doc.project_id,
            'content_path': doc.content_path,
            'metadata': doc.doc_metadata,
            'label': None,  # No relationships loaded yet
            'index_status': doc.index_status,
            'prediction': None,
            'confidence': None,
            'prediction_id': None,
            'created_at': doc.created_at,
            'updated_at': doc.updated_at,
        })

    def _convert_to_pydantic(self, doc: DocumentModel) -> Document:
        """Convert SQLAlchemy model to Pydantic model.

        Args:
            doc: SQLAlchemy document model

        Returns:
            Pydantic document model
        """
        # Get the latest prediction if available
        latest_prediction = doc.predictions[0] if doc.predictions else None

        # Get the first label if available (for backward compatibility)
        # Note: Documents can have multiple labels (one per field), this returns the first one
        first_label = None
        if doc.labels:
            first_label = doc.labels[0].field_class.name if doc.labels[0].field_class else None

        return Document.model_validate({
            'id': doc.id,
            'project_id': doc.project_id,
            'content_path': doc.content_path,
            'metadata': doc.doc_metadata,  # Map doc_metadata to metadata for Pydantic
            'label': first_label,
            'index_status': doc.index_status,
            'prediction': latest_prediction.field_class.name if latest_prediction and latest_prediction.field_class else None,
            'confidence': latest_prediction.confidence if latest_prediction else None,
            'prediction_id': latest_prediction.id if latest_prediction else None,
            'created_at': doc.created_at,
            'updated_at': doc.updated_at,
        })

    async def get_multi_by_ids(self, project_id: int, document_ids: List[int]) -> Sequence[Document]:
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

        return [self._convert_to_pydantic_simple(doc) for doc in documents]

    async def delete_multi(self, project_id: int, document_ids: List[int]) -> None:
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
            from ..core.storage import document_storage

            # Delete documents
            query = (
                select(DocumentModel)
                .where(DocumentModel.project_id == project_id)
                .where(DocumentModel.id.in_(document_ids))
            )
            result = await self.db.execute(query)
            documents = result.scalars().all()

            for doc in documents:
                # Delete from database
                await self.db.delete(doc)
                # Delete file from storage
                document_storage.delete_document(project_id, doc.id)

            await self.db.commit()
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error while deleting documents: {str(e)}"
            ) from e

    async def delete_bulk(
        self, project_id: int, delete_request: DocumentBulkDelete
    ) -> DocumentBulkDeleteResponse:
        """Delete multiple documents with detailed tracking.

        Args:
            project_id: Project ID
            delete_request: Bulk delete request with IDs and/or ranges

        Returns:
            DocumentBulkDeleteResponse with detailed results

        Raises:
            HTTPException: If validation fails
        """
        from ..core.storage import document_storage

        # Collect all document IDs to delete
        document_ids_to_delete = set()

        # Add individual IDs
        if delete_request.document_ids:
            document_ids_to_delete.update(delete_request.document_ids)

        # Add IDs from ranges
        if delete_request.ranges:
            for range_obj in delete_request.ranges:
                if range_obj.start > range_obj.end:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid range: start ({range_obj.start}) must be <= end ({range_obj.end})"
                    )
                # Add all IDs in range (inclusive)
                document_ids_to_delete.update(range(range_obj.start, range_obj.end + 1))

        # Validate that at least one deletion method is provided
        if not document_ids_to_delete:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No document IDs or ranges provided for deletion"
            )

        # Limit total documents to delete
        if len(document_ids_to_delete) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Too many documents requested for deletion: {len(document_ids_to_delete)}. Maximum is 1000."
            )

        # Track results
        results: List[DocumentDeletionResult] = []
        successful_count = 0
        failed_count = 0

        # Process each document
        for doc_id in document_ids_to_delete:
            try:
                # Try to find and delete the document
                query = (
                    select(DocumentModel)
                    .where(DocumentModel.project_id == project_id)
                    .where(DocumentModel.id == doc_id)
                )
                result = await self.db.execute(query)
                doc = result.scalar_one_or_none()

                if doc is None:
                    # Document not found
                    failed_count += 1
                    results.append(
                        DocumentDeletionResult(
                            document_id=doc_id,
                            success=False,
                            error="Document not found"
                        )
                    )
                else:
                    # Delete from database
                    await self.db.delete(doc)
                    await self.db.flush()  # Flush to catch any DB errors

                    # Delete file from storage
                    storage_deleted = document_storage.delete_document(project_id, doc_id)

                    successful_count += 1
                    results.append(
                        DocumentDeletionResult(
                            document_id=doc_id,
                            success=True,
                            error=None
                        )
                    )

            except Exception as e:
                # Individual deletion failed
                failed_count += 1
                results.append(
                    DocumentDeletionResult(
                        document_id=doc_id,
                        success=False,
                        error=str(e)
                    )
                )

        # Commit all successful deletions
        try:
            await self.db.commit()
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error while committing deletions: {str(e)}"
            ) from e

        return DocumentBulkDeleteResponse(
            total_requested=len(document_ids_to_delete),
            successful=successful_count,
            failed=failed_count,
            results=results
        )
