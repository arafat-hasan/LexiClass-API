"""Field service layer."""

import logging
from typing import Optional, Sequence


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Field
from ..schemas import FieldCreate, FieldUpdate

logger = logging.getLogger(__name__)


class FieldService:
    """Service for field operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service with database session."""
        self.db = db

    async def create(self, project_id: int, obj_in: FieldCreate) -> Field:
        """Create new field."""
        db_obj = Field(
            project_id=project_id,
            name=obj_in.name,
            description=obj_in.description,
        )
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        logger.info(
            "Created new field",
            extra={
                "field_id": field_id,
                "project_id": project_id,
                "name": obj_in.name,
            },
        )
        return db_obj

    async def get(self, field_id: int) -> Optional[Field]:
        """Get field by ID."""
        result = await self.db.execute(
            select(Field).where(Field.id == field_id)
        )
        return result.scalar_one_or_none()

    async def get_by_project(
        self,
        project_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Field]:
        """Get fields by project ID."""
        result = await self.db.execute(
            select(Field)
            .where(Field.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .order_by(Field.created_at.desc())
        )
        return result.scalars().all()

    async def update(
        self,
        db_obj: Field,
        obj_in: FieldUpdate,
    ) -> Field:
        """Update field."""
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        logger.info(
            "Updated field",
            extra={
                "field_id": db_obj.id,
                "updated_fields": list(update_data.keys()),
            },
        )
        return db_obj

    async def delete(self, db_obj: Field) -> None:
        """Delete field."""
        field_id = db_obj.id
        await self.db.delete(db_obj)
        await self.db.commit()

        logger.info(
            "Deleted field",
            extra={"field_id": field_id},
        )
