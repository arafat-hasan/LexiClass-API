"""Project model definition."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .document import Document
    from .task import Task


class Project(Base):
    """Project model for document classification jobs."""

    name: Mapped[str] = mapped_column(String(length=255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(
        String(length=50),
        default="created",
        nullable=False,
    )
    config: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    index_status: Mapped[Optional[str]] = mapped_column(
        String(length=50),
        nullable=True,
    )
    model_status: Mapped[Optional[str]] = mapped_column(
        String(length=50),
        nullable=True,
    )
    last_trained_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_indexed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    documents: Mapped[List["Document"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    tasks: Mapped[List["Task"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
