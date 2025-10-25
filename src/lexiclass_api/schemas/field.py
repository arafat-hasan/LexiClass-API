"""Field schemas for API requests and responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FieldBase(BaseModel):
    """Shared properties."""

    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class FieldCreate(FieldBase):
    """Properties to receive on field creation."""

    pass


class FieldUpdate(BaseModel):
    """Properties to receive on field update."""

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class FieldInDBBase(BaseModel):
    """Base class for all models from DB."""

    id: str
    project_id: str
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class Field(FieldInDBBase):
    """Field model for API responses."""

    pass


class FieldInDB(FieldInDBBase):
    """Additional properties stored in DB."""

    pass
