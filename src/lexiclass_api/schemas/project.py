"""Project schemas for API requests and responses."""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """Shared properties."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    config: Dict = Field(default_factory=dict)


class ProjectCreate(ProjectBase):
    """Properties to receive on project creation."""

    pass


class ProjectUpdate(ProjectBase):
    """Properties to receive on project update."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)


class ProjectInDBBase(ProjectBase):
    """Base class for all models from DB."""

    id: str
    status: str
    index_status: Optional[str] = None
    model_status: Optional[str] = None
    last_trained_at: Optional[datetime] = None
    last_indexed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class Project(ProjectInDBBase):
    """Project model for API responses."""

    pass


class ProjectInDB(ProjectInDBBase):
    """Additional properties stored in DB."""

    pass
