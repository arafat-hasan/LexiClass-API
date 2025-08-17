"""Task schemas for API requests and responses."""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    """Shared properties."""

    type: str = Field(..., max_length=50)
    status: str = Field(default="pending", max_length=50)
    progress: Optional[int] = Field(None, ge=0, le=100)


class TaskCreate(TaskBase):
    """Properties to receive on task creation."""

    project_id: str
    celery_id: str


class TaskUpdate(TaskBase):
    """Properties to receive on task update."""

    status: Optional[str] = Field(None, max_length=50)
    result: Optional[Dict] = None
    error: Optional[str] = None
    progress: Optional[int] = Field(None, ge=0, le=100)


class TaskInDBBase(TaskBase):
    """Base class for all models from DB."""

    id: str
    project_id: str
    celery_id: str
    result: Optional[Dict] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class Task(TaskInDBBase):
    """Task model for API responses."""

    pass


class TaskInDB(TaskInDBBase):
    """Additional properties stored in DB."""

    pass


class TaskStatus(BaseModel):
    """Task status response."""

    id: str
    status: str
    progress: Optional[int] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
