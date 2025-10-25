"""DocumentLabel model definition."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .document import Document
    from .field import Field
    from .field_class import FieldClass


class DocumentLabel(Base):
    """DocumentLabel model for manual labels.

    Stores manual labels assigned to documents for training purposes.
    Each document can have one label per field.
    """

    __tablename__ = "document_label"

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
    class_id: Mapped[str] = mapped_column(
        ForeignKey("field_class.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_training_data: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    # Relationships
    document: Mapped["Document"] = relationship(back_populates="labels")
    field: Mapped["Field"] = relationship()
    field_class: Mapped["FieldClass"] = relationship(back_populates="labels")

    # Unique constraint: one label per document per field
    __table_args__ = (
        UniqueConstraint("document_id", "field_id", name="uq_document_field_label"),
    )
