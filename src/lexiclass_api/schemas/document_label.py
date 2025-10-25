"""DocumentLabel schemas for API requests and responses."""

from datetime import datetime

from pydantic import BaseModel


class DocumentLabelCreate(BaseModel):
    """Properties to receive on document label creation."""

    field_id: str
    class_id: str
    is_training_data: bool = True


class DocumentLabelUpdate(BaseModel):
    """Properties to receive on document label update."""

    class_id: str
    is_training_data: bool = True


class DocumentLabelInDBBase(BaseModel):
    """Base class for all models from DB."""

    id: str
    document_id: str
    field_id: str
    class_id: str
    is_training_data: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class DocumentLabel(DocumentLabelInDBBase):
    """DocumentLabel model for API responses."""

    pass


class DocumentLabelInDB(DocumentLabelInDBBase):
    """Additional properties stored in DB."""

    pass
