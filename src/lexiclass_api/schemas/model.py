"""Model schemas for API requests and responses."""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel

from ..models import ModelStatus


class ModelInDBBase(BaseModel):
    """Base class for all models from DB."""

    id: str
    field_id: str
    version: int
    model_path: str
    vectorizer_path: Optional[str]
    accuracy: Optional[float]
    metrics: Optional[Dict]
    status: ModelStatus
    trained_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class Model(ModelInDBBase):
    """Model model for API responses."""

    pass


class ModelInDB(ModelInDBBase):
    """Additional properties stored in DB."""

    pass


class ModelCreate(BaseModel):
    """Properties to receive on model creation."""

    version: int
    model_path: str
    vectorizer_path: Optional[str] = None
    accuracy: Optional[float] = None
    metrics: Optional[Dict] = None
    status: ModelStatus
    trained_at: Optional[datetime] = None


class ModelUpdate(BaseModel):
    """Properties to receive on model update."""

    model_path: Optional[str] = None
    vectorizer_path: Optional[str] = None
    accuracy: Optional[float] = None
    metrics: Optional[Dict] = None
    status: Optional[ModelStatus] = None
    trained_at: Optional[datetime] = None
