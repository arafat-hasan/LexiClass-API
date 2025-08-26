"""Document schemas for API requests and responses."""

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class DocumentBase(BaseModel):
    """Shared properties."""

    metadata: Dict = Field(default_factory=dict)
    label: Optional[str] = Field(None, max_length=255)


class DocumentCreate(BaseModel):
    """Properties to receive on document creation."""

    id: Optional[str] = None
    content: str = Field(..., min_length=1)
    metadata: Dict = Field(default_factory=dict)
    label: Optional[str] = Field(None, max_length=255)

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that the ID is a valid UUID if provided."""
        if v is not None:
            try:
                UUID(v)
            except ValueError:
                raise ValueError("Document ID must be a valid UUID")
        return v





class DocumentUpdate(BaseModel):
    """Properties to receive on document update."""

    content: Optional[str] = None
    metadata: Optional[Dict] = None
    label: Optional[str] = Field(None, max_length=255)


class DocumentInDBBase(BaseModel):
    """Base class for all models from DB."""

    id: str
    project_id: str
    content_path: str
    metadata: Dict = Field(default_factory=dict)
    label: Optional[str] = Field(None, max_length=255)
    status: str
    prediction: Optional[str] = None
    confidence: Optional[float] = None
    prediction_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class Document(DocumentInDBBase):
    """Document model for API responses."""

    pass


class DocumentInDB(DocumentInDBBase):
    """Additional properties stored in DB."""

    pass


class DocumentBulkCreate(BaseModel):
    """Bulk document creation."""

    documents: list[DocumentCreate] = Field(..., min_items=1, max_items=1000)
