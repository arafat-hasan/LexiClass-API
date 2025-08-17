"""Document service."""

from typing import List, Optional, Sequence

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
        # Create document models
        db_documents = [
            DocumentModel(
                project_id=project_id,
                id=doc.id or str(i),  # Use provided ID or generate one
                content=doc.content,
                metadata=doc.doc_metadata,
                label=doc.label,
                status="pending",
            )
            for i, doc in enumerate(documents_in.documents)
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
