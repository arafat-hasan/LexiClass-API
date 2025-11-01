"""DocumentLabel service layer."""

import logging
from typing import List, Optional, Sequence


from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import DocumentLabel
from ..schemas import (
    DocumentLabelCreate,
    DocumentLabelUpdate,
    DocumentLabelBulkCreate,
    DocumentLabelBulkResponse,
    LabelOperationResult,
    DocumentLabelBulkDelete,
    DocumentLabelBulkDeleteResponse,
    LabelDeletionResult,
)

logger = logging.getLogger(__name__)


class DocumentLabelService:
    """Service for document label operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service with database session."""
        self.db = db

    async def create(
        self, document_id: int, obj_in: DocumentLabelCreate
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
        db_obj = DocumentLabel(
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
                "label_id": db_obj.id,
                "document_id": document_id,
                "field_id": obj_in.field_id,
                "class_id": obj_in.class_id,
            },
        )
        return db_obj

    async def get(self, label_id: int) -> Optional[DocumentLabel]:
        """Get document label by ID."""
        result = await self.db.execute(
            select(DocumentLabel).where(DocumentLabel.id == label_id)
        )
        return result.scalar_one_or_none()

    async def get_by_document(
        self,
        document_id: int,
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
        self, document_id: int, field_id: int
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
        field_id: int,
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

    async def create_bulk(
        self, bulk_create: DocumentLabelBulkCreate
    ) -> DocumentLabelBulkResponse:
        """Create multiple document labels with detailed tracking.

        Args:
            bulk_create: Bulk create request with field_id and labels

        Returns:
            DocumentLabelBulkResponse with detailed results

        Raises:
            HTTPException: If validation fails
        """
        if not bulk_create.labels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No labels provided for bulk creation"
            )

        if len(bulk_create.labels) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Too many labels requested: {len(bulk_create.labels)}. Maximum is 1000."
            )

        # Track results
        results: List[LabelOperationResult] = []
        successful_count = 0
        failed_count = 0

        # Process each label
        for label_item in bulk_create.labels:
            try:
                # Create DocumentLabelCreate instance
                label_create = DocumentLabelCreate(
                    field_id=bulk_create.field_id,
                    class_id=label_item.class_id,
                    is_training_data=label_item.is_training_data
                )

                # Create or update the label
                await self.create(label_item.document_id, label_create)

                successful_count += 1
                results.append(
                    LabelOperationResult(
                        document_id=label_item.document_id,
                        success=True,
                        error=None
                    )
                )

            except Exception as e:
                # Individual label creation failed
                failed_count += 1
                results.append(
                    LabelOperationResult(
                        document_id=label_item.document_id,
                        success=False,
                        error=str(e)
                    )
                )

        return DocumentLabelBulkResponse(
            total_requested=len(bulk_create.labels),
            successful=successful_count,
            failed=failed_count,
            results=results
        )

    async def delete_bulk(
        self, delete_request: DocumentLabelBulkDelete
    ) -> DocumentLabelBulkDeleteResponse:
        """Delete multiple labels with detailed tracking.

        Args:
            delete_request: Bulk delete request with IDs and/or ranges

        Returns:
            DocumentLabelBulkDeleteResponse with detailed results

        Raises:
            HTTPException: If validation fails
        """
        # Collect all label IDs to delete
        label_ids_to_delete = set()

        # Add individual IDs
        if delete_request.label_ids:
            label_ids_to_delete.update(delete_request.label_ids)

        # Add IDs from ranges
        if delete_request.ranges:
            for range_obj in delete_request.ranges:
                if range_obj.start > range_obj.end:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid range: start ({range_obj.start}) must be <= end ({range_obj.end})"
                    )
                # Add all IDs in range (inclusive)
                label_ids_to_delete.update(range(range_obj.start, range_obj.end + 1))

        # Validate that at least one deletion method is provided
        if not label_ids_to_delete:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No label IDs or ranges provided for deletion"
            )

        # Limit total labels to delete
        if len(label_ids_to_delete) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Too many labels requested for deletion: {len(label_ids_to_delete)}. Maximum is 1000."
            )

        # Track results
        results: List[LabelDeletionResult] = []
        successful_count = 0
        failed_count = 0

        # Process each label
        for label_id in label_ids_to_delete:
            try:
                # Try to find and delete the label
                label = await self.get(label_id)

                if label is None:
                    # Label not found
                    failed_count += 1
                    results.append(
                        LabelDeletionResult(
                            label_id=label_id,
                            success=False,
                            error="Label not found"
                        )
                    )
                else:
                    # Delete the label
                    await self.delete(label)

                    successful_count += 1
                    results.append(
                        LabelDeletionResult(
                            label_id=label_id,
                            success=True,
                            error=None
                        )
                    )

            except Exception as e:
                # Individual deletion failed
                failed_count += 1
                results.append(
                    LabelDeletionResult(
                        label_id=label_id,
                        success=False,
                        error=str(e)
                    )
                )

        return DocumentLabelBulkDeleteResponse(
            total_requested=len(label_ids_to_delete),
            successful=successful_count,
            failed=failed_count,
            results=results
        )
