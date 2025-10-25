"""FieldClass model definition."""

from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .document_label import DocumentLabel
    from .field import Field
    from .prediction import Prediction


class FieldClass(Base):
    """FieldClass model for classification values.

    A FieldClass represents a possible value/outcome for a Field
    (e.g., "Yes"/"No" for a binary field, or "High"/"Mid"/"Low" for a multi-class field).
    """

    __tablename__ = "field_class"

    field_id: Mapped[str] = mapped_column(
        ForeignKey("field.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    field: Mapped["Field"] = relationship(back_populates="classes")
    labels: Mapped[List["DocumentLabel"]] = relationship(
        back_populates="field_class",
        cascade="all, delete-orphan",
    )
    predictions: Mapped[List["Prediction"]] = relationship(
        back_populates="field_class",
        cascade="all, delete-orphan",
    )
