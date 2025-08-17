"""Document schemas for API requests and responses."""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    """Shared properties."""

    content: str = Field(..., min_length=1)
    metadata: Dict = Field(default_factory=dict)
    label: Optional[str] = Field(None, max_length=255)


class DocumentCreate(DocumentBase):
    """Properties to receive on document creation."""

    id: Optional[str] = None


class DocumentUpdate(DocumentBase):
    """Properties to receive on document update."""

    content: Optional[str] = None
    label: Optional[str] = None


class DocumentInDBBase(DocumentBase):
    """Base class for all models from DB."""

    id: str
    project_id: str
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
