"""Project service layer."""

import logging
from typing import Optional, Sequence
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.project import Project
from ..schemas.project import ProjectCreate, ProjectUpdate

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for project operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service with database session."""
        self.db = db

    async def create(self, obj_in: ProjectCreate) -> Project:
        """Create new project."""
        project_id = str(uuid4())
        db_obj = Project(
            id=project_id,
            name=obj_in.name,
            description=obj_in.description,
            config=obj_in.config,
        )
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        
        logger.info(
            "Created new project",
            extra={
                "project_id": project_id,
                "name": obj_in.name,
            },
        )
        return db_obj

    async def get(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Project]:
        """Get multiple projects."""
        result = await self.db.execute(
            select(Project)
            .offset(skip)
            .limit(limit)
            .order_by(Project.created_at.desc())
        )
        return result.scalars().all()

    async def update(
        self,
        db_obj: Project,
        obj_in: ProjectUpdate,
    ) -> Project:
        """Update project."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        logger.info(
            "Updated project",
            extra={
                "project_id": db_obj.id,
                "updated_fields": list(update_data.keys()),
            },
        )
        return db_obj

    async def delete(self, db_obj: Project) -> None:
        """Delete project."""
        project_id = db_obj.id
        await self.db.delete(db_obj)
        await self.db.commit()

        logger.info(
            "Deleted project",
            extra={"project_id": project_id},
        )

    async def update_status(
        self,
        project_id: str,
        status: str,
        *,
        index_status: Optional[str] = None,
        model_status: Optional[str] = None,
    ) -> Optional[Project]:
        """Update project status."""
        project = await self.get(project_id)
        if not project:
            return None

        project.status = status
        if index_status is not None:
            project.index_status = index_status
        if model_status is not None:
            project.model_status = model_status

        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)

        logger.info(
            "Updated project status",
            extra={
                "project_id": project_id,
                "status": status,
                "index_status": index_status,
                "model_status": model_status,
            },
        )
        return project
