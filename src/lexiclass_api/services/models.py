"""Model service layer."""

import logging
from typing import Optional, Sequence
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.model import Model, ModelStatus
from ..schemas.model import ModelCreate, ModelUpdate

logger = logging.getLogger(__name__)


class ModelService:
    """Service for model operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service with database session."""
        self.db = db

    async def create(self, field_id: str, obj_in: ModelCreate) -> Model:
        """Create new model."""
        model_id = str(uuid4())
        db_obj = Model(
            id=model_id,
            field_id=field_id,
            version=obj_in.version,
            model_path=obj_in.model_path,
            vectorizer_path=obj_in.vectorizer_path,
            accuracy=obj_in.accuracy,
            metrics=obj_in.metrics,
            status=obj_in.status,
            trained_at=obj_in.trained_at,
        )
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        logger.info(
            "Created new model",
            extra={
                "model_id": model_id,
                "field_id": field_id,
                "version": obj_in.version,
            },
        )
        return db_obj

    async def get(self, model_id: str) -> Optional[Model]:
        """Get model by ID."""
        result = await self.db.execute(
            select(Model).where(Model.id == model_id)
        )
        return result.scalar_one_or_none()

    async def get_by_field(
        self,
        field_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Model]:
        """Get models by field ID."""
        result = await self.db.execute(
            select(Model)
            .where(Model.field_id == field_id)
            .offset(skip)
            .limit(limit)
            .order_by(Model.version.desc())
        )
        return result.scalars().all()

    async def get_latest_by_field(self, field_id: str) -> Optional[Model]:
        """Get latest model by field ID."""
        result = await self.db.execute(
            select(Model)
            .where(Model.field_id == field_id)
            .order_by(Model.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_latest_ready_by_field(self, field_id: str) -> Optional[Model]:
        """Get latest ready model by field ID."""
        result = await self.db.execute(
            select(Model)
            .where(Model.field_id == field_id)
            .where(Model.status == ModelStatus.READY)
            .order_by(Model.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        db_obj: Model,
        obj_in: ModelUpdate,
    ) -> Model:
        """Update model."""
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        logger.info(
            "Updated model",
            extra={
                "model_id": db_obj.id,
                "updated_fields": list(update_data.keys()),
            },
        )
        return db_obj

    async def delete(self, db_obj: Model) -> None:
        """Delete model."""
        model_id = db_obj.id
        await self.db.delete(db_obj)
        await self.db.commit()

        logger.info(
            "Deleted model",
            extra={"model_id": model_id},
        )

    async def delete_old_models(self, field_id: str, keep_latest: int = 1) -> int:
        """Delete old models for a field, keeping only the latest N models.

        Args:
            field_id: Field ID
            keep_latest: Number of latest models to keep

        Returns:
            Number of models deleted
        """
        # Get all models for the field ordered by version desc
        models = await self.get_by_field(field_id, limit=1000)

        # Skip the latest N models
        models_to_delete = list(models)[keep_latest:]

        # Delete old models
        for model in models_to_delete:
            await self.delete(model)

        logger.info(
            "Deleted old models",
            extra={
                "field_id": field_id,
                "deleted_count": len(models_to_delete),
            },
        )

        return len(models_to_delete)
