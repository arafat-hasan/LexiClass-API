"""Document model definition."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .project import Project


class Document(Base):
    """Document model for text classification."""

    project_id: Mapped[str] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    label: Mapped[Optional[str]] = mapped_column(
        String(length=255),
        nullable=True,
    )
    prediction: Mapped[Optional[str]] = mapped_column(
        String(length=255),
        nullable=True,
    )
    confidence: Mapped[Optional[float]] = mapped_column(
        nullable=True,
    )
    prediction_id: Mapped[Optional[str]] = mapped_column(
        String(length=255),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(length=50),
        default="pending",
        nullable=False,
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="documents")
