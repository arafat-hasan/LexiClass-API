"""FieldClass service layer."""

import logging
from typing import Optional, Sequence
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.field_class import FieldClass
from ..schemas.field_class import FieldClassCreate, FieldClassUpdate

logger = logging.getLogger(__name__)


class FieldClassService:
    """Service for field class operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service with database session."""
        self.db = db

    async def create(self, field_id: str, obj_in: FieldClassCreate) -> FieldClass:
        """Create new field class."""
        class_id = str(uuid4())
        db_obj = FieldClass(
            id=class_id,
            field_id=field_id,
            name=obj_in.name,
        )
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        logger.info(
            "Created new field class",
            extra={
                "class_id": class_id,
                "field_id": field_id,
                "name": obj_in.name,
            },
        )
        return db_obj

    async def get(self, class_id: str) -> Optional[FieldClass]:
        """Get field class by ID."""
        result = await self.db.execute(
            select(FieldClass).where(FieldClass.id == class_id)
        )
        return result.scalar_one_or_none()

    async def get_by_field(
        self,
        field_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[FieldClass]:
        """Get classes by field ID."""
        result = await self.db.execute(
            select(FieldClass)
            .where(FieldClass.field_id == field_id)
            .offset(skip)
            .limit(limit)
            .order_by(FieldClass.created_at.asc())
        )
        return result.scalars().all()

    async def update(
        self,
        db_obj: FieldClass,
        obj_in: FieldClassUpdate,
    ) -> FieldClass:
        """Update field class."""
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        logger.info(
            "Updated field class",
            extra={
                "class_id": db_obj.id,
                "updated_fields": list(update_data.keys()),
            },
        )
        return db_obj

    async def delete(self, db_obj: FieldClass) -> None:
        """Delete field class."""
        class_id = db_obj.id
        await self.db.delete(db_obj)
        await self.db.commit()

        logger.info(
            "Deleted field class",
            extra={"class_id": class_id},
        )
