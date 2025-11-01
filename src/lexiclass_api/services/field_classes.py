"""FieldClass service layer."""

import logging
from typing import Optional, Sequence


from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import FieldClass
from ..schemas import FieldClassCreate, FieldClassUpdate

logger = logging.getLogger(__name__)


class FieldClassService:
    """Service for field class operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service with database session."""
        self.db = db

    async def _check_duplicate_name(
        self, field_id: int, name: str, exclude_id: Optional[int] = None
    ) -> None:
        """Check if a class with the same name already exists in the field.

        Args:
            field_id: Field ID
            name: Class name to check
            exclude_id: Optional class ID to exclude from check (for updates)

        Raises:
            HTTPException: If duplicate name found
        """
        query = select(FieldClass).where(
            FieldClass.field_id == field_id,
            FieldClass.name == name
        )
        if exclude_id:
            query = query.where(FieldClass.id != exclude_id)

        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Class with name '{name}' already exists in this field"
            )

    async def create(self, field_id: int, obj_in: FieldClassCreate) -> FieldClass:
        """Create new field class."""
        # Check for duplicate class name
        await self._check_duplicate_name(field_id, obj_in.name)

        db_obj = FieldClass(
            field_id=field_id,
            name=obj_in.name,
        )
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        logger.info(
            "Created new field class",
            extra={
                "class_id": db_obj.id,
                "field_id": field_id,
                "name": obj_in.name,
            },
        )
        return db_obj

    async def get(self, class_id: int) -> Optional[FieldClass]:
        """Get field class by ID."""
        result = await self.db.execute(
            select(FieldClass).where(FieldClass.id == class_id)
        )
        return result.scalar_one_or_none()

    async def get_by_field(
        self,
        field_id: int,
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

        # Check for duplicate name if name is being updated
        if "name" in update_data:
            await self._check_duplicate_name(
                db_obj.field_id,
                update_data["name"],
                exclude_id=db_obj.id
            )

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
