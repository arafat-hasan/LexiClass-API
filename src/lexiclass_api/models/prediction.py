"""Prediction model definition."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .document import Document
    from .field import Field
    from .field_class import FieldClass
    from .model import Model


class Prediction(Base):
    """Prediction model for machine-generated predictions.

    Stores predictions made by trained models for documents.
    Each document can have one prediction per field (the latest one).
    """

    document_id: Mapped[str] = mapped_column(
        ForeignKey("document.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field_id: Mapped[str] = mapped_column(
        ForeignKey("field.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_id: Mapped[str] = mapped_column(
        ForeignKey("model.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    class_id: Mapped[str] = mapped_column(
        ForeignKey("field_class.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    confidence: Mapped[Optional[float]] = mapped_column(nullable=True)
    pred_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata",  # Column name in database
        JSON,
        default=dict,
        nullable=True,
    )

    # Relationships
    document: Mapped["Document"] = relationship(back_populates="predictions")
    field: Mapped["Field"] = relationship()
    field_class: Mapped["FieldClass"] = relationship(back_populates="predictions")
    model: Mapped["Model"] = relationship(back_populates="predictions")

    # Unique constraint: one prediction per document per field (latest only)
    __table_args__ = (
        UniqueConstraint("document_id", "field_id", name="uq_document_field_prediction"),
    )
