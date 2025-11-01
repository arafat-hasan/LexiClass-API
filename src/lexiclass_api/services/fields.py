"""Field service layer."""

import logging
from typing import Optional, Sequence


from fastapi import HTTPException, status
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

    async def _check_duplicate_name(
        self, project_id: int, name: str, exclude_id: Optional[int] = None
    ) -> None:
        """Check if a field with the same name already exists in the project.

        Args:
            project_id: Project ID
            name: Field name to check
            exclude_id: Optional field ID to exclude from check (for updates)

        Raises:
            HTTPException: If duplicate name found
        """
        query = select(Field).where(
            Field.project_id == project_id,
            Field.name == name
        )
        if exclude_id:
            query = query.where(Field.id != exclude_id)

        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Field with name '{name}' already exists in this project"
            )

    async def create(self, project_id: int, obj_in: FieldCreate) -> Field:
        """Create new field and optionally create classes for it."""
        from ..models import FieldClass as FieldClassModel
        from ..schemas import FieldClassCreate

        # Check for duplicate field name
        await self._check_duplicate_name(project_id, obj_in.name)

        # Check for duplicate class names within the provided classes
        if obj_in.classes:
            class_names = [name.strip() for name in obj_in.classes]
            if len(class_names) != len(set(class_names)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Duplicate class names provided"
                )

        db_obj = Field(
            project_id=project_id,
            name=obj_in.name,
            description=obj_in.description,
        )
        self.db.add(db_obj)
        await self.db.flush()  # Get the field ID before creating classes

        # Create classes if provided
        if obj_in.classes:
            from ..services.field_classes import FieldClassService
            class_service = FieldClassService(self.db)

            for class_name in class_names:
                class_create = FieldClassCreate(name=class_name)
                await class_service.create(db_obj.id, class_create)

        await self.db.commit()
        await self.db.refresh(db_obj)

        logger.info(
            "Created new field",
            extra={
                "field_id": db_obj.id,
                "project_id": project_id,
                "name": obj_in.name,
                "classes_count": len(obj_in.classes) if obj_in.classes else 0,
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

        # Check for duplicate name if name is being updated
        if "name" in update_data:
            await self._check_duplicate_name(
                db_obj.project_id,
                update_data["name"],
                exclude_id=db_obj.id
            )

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
