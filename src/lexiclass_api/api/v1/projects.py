"""Project API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.deps import get_db
from ...schemas import Project, ProjectCreate, ProjectUpdate
from ...services.projects import ProjectService

router = APIRouter()


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED, tags=["projects"])
async def create_project(
    *,
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),

) -> Project:
    """Create new project."""
    service = ProjectService(db)
    project = await service.create(project_in)
    return project


@router.get("/{project_id}", response_model=Project, tags=["projects"])
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),

) -> Project:
    """Get project by ID."""
    service = ProjectService(db)
    project = await service.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


@router.get("/", response_model=List[Project], tags=["projects"])
async def list_projects(
    *,
    db: AsyncSession = Depends(get_db),

    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> List[Project]:
    """List projects."""
    service = ProjectService(db)
    projects = await service.get_multi(skip=skip, limit=limit)
    return list(projects)


@router.put("/{project_id}", response_model=Project, tags=["projects"])
async def update_project(
    *,
    project_id: int,
    project_in: ProjectUpdate,
    db: AsyncSession = Depends(get_db),

) -> Project:
    """Update project."""
    service = ProjectService(db)
    project = await service.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    project = await service.update(project, project_in)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["projects"])
async def delete_project(
    *,
    project_id: int,
    db: AsyncSession = Depends(get_db),

) -> None:
    """Delete project."""
    service = ProjectService(db)
    project = await service.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    await service.delete(project)
