"""DocumentLabel service layer."""

import logging
from typing import Optional, Sequence
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import DocumentLabel
from ..schemas.document_label import DocumentLabelCreate, DocumentLabelUpdate

logger = logging.getLogger(__name__)


class DocumentLabelService:
    """Service for document label operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service with database session."""
        self.db = db

    async def create(
        self, document_id: str, obj_in: DocumentLabelCreate
    ) -> DocumentLabel:
        """Create new document label.

        If a label already exists for this document and field, it will be replaced.
        """
        # Check if label already exists for this document and field
        existing = await self.get_by_document_and_field(
            document_id, obj_in.field_id
        )

        if existing:
            # Update existing label
            return await self.update(
                existing,
                DocumentLabelUpdate(
                    class_id=obj_in.class_id,
                    is_training_data=obj_in.is_training_data,
                ),
            )

        # Create new label
        label_id = str(uuid4())
        db_obj = DocumentLabel(
            id=label_id,
            document_id=document_id,
            field_id=obj_in.field_id,
            class_id=obj_in.class_id,
            is_training_data=obj_in.is_training_data,
        )
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        logger.info(
            "Created new document label",
            extra={
                "label_id": label_id,
                "document_id": document_id,
                "field_id": obj_in.field_id,
                "class_id": obj_in.class_id,
            },
        )
        return db_obj

    async def get(self, label_id: str) -> Optional[DocumentLabel]:
        """Get document label by ID."""
        result = await self.db.execute(
            select(DocumentLabel).where(DocumentLabel.id == label_id)
        )
        return result.scalar_one_or_none()

    async def get_by_document(
        self,
        document_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[DocumentLabel]:
        """Get labels by document ID."""
        result = await self.db.execute(
            select(DocumentLabel)
            .where(DocumentLabel.document_id == document_id)
            .offset(skip)
            .limit(limit)
            .order_by(DocumentLabel.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_document_and_field(
        self, document_id: str, field_id: str
    ) -> Optional[DocumentLabel]:
        """Get label by document ID and field ID."""
        result = await self.db.execute(
            select(DocumentLabel)
            .where(DocumentLabel.document_id == document_id)
            .where(DocumentLabel.field_id == field_id)
        )
        return result.scalar_one_or_none()

    async def get_by_field(
        self,
        field_id: str,
        *,
        is_training_data: Optional[bool] = None,
        skip: int = 0,
        limit: int = 1000,
    ) -> Sequence[DocumentLabel]:
        """Get labels by field ID."""
        query = select(DocumentLabel).where(DocumentLabel.field_id == field_id)

        if is_training_data is not None:
            query = query.where(DocumentLabel.is_training_data == is_training_data)

        result = await self.db.execute(
            query.offset(skip).limit(limit).order_by(DocumentLabel.created_at.desc())
        )
        return result.scalars().all()

    async def update(
        self,
        db_obj: DocumentLabel,
        obj_in: DocumentLabelUpdate,
    ) -> DocumentLabel:
        """Update document label."""
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        logger.info(
            "Updated document label",
            extra={
                "label_id": db_obj.id,
                "updated_fields": list(update_data.keys()),
            },
        )
        return db_obj

    async def delete(self, db_obj: DocumentLabel) -> None:
        """Delete document label."""
        label_id = db_obj.id
        await self.db.delete(db_obj)
        await self.db.commit()

        logger.info(
            "Deleted document label",
            extra={"label_id": label_id},
        )
