"""FieldClass schemas for API requests and responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FieldClassBase(BaseModel):
    """Shared properties."""

    name: str = Field(..., max_length=255)


class FieldClassCreate(FieldClassBase):
    """Properties to receive on field class creation."""

    pass


class FieldClassUpdate(BaseModel):
    """Properties to receive on field class update."""

    name: Optional[str] = Field(None, max_length=255)


class FieldClassInDBBase(BaseModel):
    """Base class for all models from DB."""

    id: str
    field_id: str
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class FieldClass(FieldClassInDBBase):
    """FieldClass model for API responses."""

    pass


class FieldClassInDB(FieldClassInDBBase):
    """Additional properties stored in DB."""

    pass
