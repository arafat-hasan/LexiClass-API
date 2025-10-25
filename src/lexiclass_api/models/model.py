"""Model model definition."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Enum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .field import Field
    from .prediction import Prediction


class ModelStatus(str, enum.Enum):
    """Model training status."""

    TRAINING = "training"
    READY = "ready"
    FAILED = "failed"


class Model(Base):
    """Model model for trained classification models.

    Stores metadata and paths for trained models.
    Each field can have one active model (latest version).
    """

    field_id: Mapped[str] = mapped_column(
        ForeignKey("field.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(nullable=False)
    model_path: Mapped[str] = mapped_column(String(512), nullable=False)
    vectorizer_path: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )
    accuracy: Mapped[Optional[float]] = mapped_column(nullable=True)
    metrics: Mapped[Optional[dict]] = mapped_column(
        JSON,
        default=dict,
        nullable=True,
    )
    status: Mapped[ModelStatus] = mapped_column(
        Enum(ModelStatus, native_enum=False, length=50),
        nullable=False,
    )
    trained_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    field: Mapped["Field"] = relationship(back_populates="models")
    predictions: Mapped[List["Prediction"]] = relationship(
        back_populates="model",
        cascade="all, delete-orphan",
    )
