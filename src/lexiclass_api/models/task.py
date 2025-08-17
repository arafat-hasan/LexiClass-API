"""Task model definition."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .project import Project


class Task(Base):
    """Task model for tracking ML operations."""

    project_id: Mapped[str] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    celery_id: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
        unique=True,
        index=True,
    )
    type: Mapped[str] = mapped_column(
        String(length=50),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(length=50),
        default="pending",
        nullable=False,
    )
    result: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    error: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
    )
    progress: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="tasks")
