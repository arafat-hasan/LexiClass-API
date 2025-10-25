"""Prediction service layer."""

import logging
from typing import Optional, Sequence
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.prediction import Prediction
from ..schemas.prediction import PredictionCreate, PredictionUpdate

logger = logging.getLogger(__name__)


class PredictionService:
    """Service for prediction operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service with database session."""
        self.db = db

    async def create(self, obj_in: PredictionCreate) -> Prediction:
        """Create new prediction.

        If a prediction already exists for this document and field, it will be replaced.
        """
        # Check if prediction already exists for this document and field
        existing = await self.get_by_document_and_field(
            obj_in.document_id, obj_in.field_id
        )

        if existing:
            # Update existing prediction
            return await self.update(
                existing,
                PredictionUpdate(
                    class_id=obj_in.class_id,
                    confidence=obj_in.confidence,
                    pred_metadata=obj_in.pred_metadata,
                ),
            )

        # Create new prediction
        prediction_id = str(uuid4())
        db_obj = Prediction(
            id=prediction_id,
            document_id=obj_in.document_id,
            field_id=obj_in.field_id,
            model_id=obj_in.model_id,
            class_id=obj_in.class_id,
            confidence=obj_in.confidence,
            pred_metadata=obj_in.pred_metadata,
        )
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        logger.info(
            "Created new prediction",
            extra={
                "prediction_id": prediction_id,
                "document_id": obj_in.document_id,
                "field_id": obj_in.field_id,
                "class_id": obj_in.class_id,
            },
        )
        return db_obj

    async def get(self, prediction_id: str) -> Optional[Prediction]:
        """Get prediction by ID."""
        result = await self.db.execute(
            select(Prediction).where(Prediction.id == prediction_id)
        )
        return result.scalar_one_or_none()

    async def get_by_document(
        self,
        document_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Prediction]:
        """Get predictions by document ID."""
        result = await self.db.execute(
            select(Prediction)
            .where(Prediction.document_id == document_id)
            .offset(skip)
            .limit(limit)
            .order_by(Prediction.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_document_and_field(
        self, document_id: str, field_id: str
    ) -> Optional[Prediction]:
        """Get prediction by document ID and field ID."""
        result = await self.db.execute(
            select(Prediction)
            .where(Prediction.document_id == document_id)
            .where(Prediction.field_id == field_id)
        )
        return result.scalar_one_or_none()

    async def get_by_field(
        self,
        field_id: str,
        *,
        skip: int = 0,
        limit: int = 1000,
    ) -> Sequence[Prediction]:
        """Get predictions by field ID."""
        result = await self.db.execute(
            select(Prediction)
            .where(Prediction.field_id == field_id)
            .offset(skip)
            .limit(limit)
            .order_by(Prediction.created_at.desc())
        )
        return result.scalars().all()

    async def update(
        self,
        db_obj: Prediction,
        obj_in: PredictionUpdate,
    ) -> Prediction:
        """Update prediction."""
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        logger.info(
            "Updated prediction",
            extra={
                "prediction_id": db_obj.id,
                "updated_fields": list(update_data.keys()),
            },
        )
        return db_obj

    async def delete(self, db_obj: Prediction) -> None:
        """Delete prediction."""
        prediction_id = db_obj.id
        await self.db.delete(db_obj)
        await self.db.commit()

        logger.info(
            "Deleted prediction",
            extra={"prediction_id": prediction_id},
        )
