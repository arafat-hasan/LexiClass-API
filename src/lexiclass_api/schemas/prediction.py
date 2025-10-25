"""Prediction schemas for API requests and responses."""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel


class PredictionInDBBase(BaseModel):
    """Base class for all models from DB."""

    id: str
    document_id: str
    field_id: str
    model_id: str
    class_id: str
    confidence: Optional[float]
    pred_metadata: Optional[Dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class Prediction(PredictionInDBBase):
    """Prediction model for API responses."""

    pass


class PredictionInDB(PredictionInDBBase):
    """Additional properties stored in DB."""

    pass


class PredictionCreate(BaseModel):
    """Properties to receive on prediction creation."""

    document_id: str
    field_id: str
    model_id: str
    class_id: str
    confidence: Optional[float] = None
    pred_metadata: Optional[Dict] = None


class PredictionUpdate(BaseModel):
    """Properties to receive on prediction update."""

    class_id: Optional[str] = None
    confidence: Optional[float] = None
    pred_metadata: Optional[Dict] = None
