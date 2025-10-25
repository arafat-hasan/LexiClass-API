"""Document model definition."""

import enum
from typing import TYPE_CHECKING, Optional, ClassVar

from sqlalchemy import JSON, Enum, ForeignKey, String, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from ..core.storage import document_storage


class IndexStatus(str, enum.Enum):
    """Document indexing status."""

    PENDING = "pending"
    INDEXED = "indexed"
    FAILED = "failed"

if TYPE_CHECKING:
    from .document_label import DocumentLabel
    from .prediction import Prediction
    from .project import Project


class Document(Base):
    """Document model for text classification."""

    project_id: Mapped[str] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content_path: Mapped[str] = mapped_column(String(512), nullable=False)
    _content: ClassVar[Optional[str]] = None  # Cache for document content

    @property
    def content(self) -> Optional[str]:
        """Get document content from storage."""
        if self._content is None and self.id:  # Only load if we have an ID
            self._content = document_storage.read_document(self.project_id, self.id)
        return self._content

    @content.setter
    def content(self, value: str) -> None:
        """Set document content and store in filesystem."""
        self._content = value
        # If we have an ID, store immediately, otherwise it will be stored after insert
        if self.id:
            document_storage.store_document(self.project_id, self.id, value)
    doc_metadata: Mapped[dict] = mapped_column(
        "metadata",  # Keep the column name in database
        JSON,
        default=dict,
        nullable=False,
    )
    index_status: Mapped[IndexStatus] = mapped_column(
        Enum(IndexStatus, native_enum=False, length=50),
        default=IndexStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="documents")
    labels: Mapped[list["DocumentLabel"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


# SQLAlchemy event listeners
@event.listens_for(Document, "after_insert")
def store_document_after_insert(mapper, connection, target):
    """Store document content after insert."""
    if target._content is not None:
        path = document_storage.store_document(target.project_id, target.id, target._content)
        target.content_path = str(path)
        # Update content_path in database
        connection.execute(
            Document.__table__.update().where(Document.id == target.id),
            {"content_path": str(path)}
        )

@event.listens_for(Document, "before_delete")
def delete_document_before_delete(mapper, connection, target):
    """Delete document content before deleting the record."""
    document_storage.delete_document(target.project_id, target.id)
