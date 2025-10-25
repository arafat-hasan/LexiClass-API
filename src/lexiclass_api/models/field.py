"""Field model definition."""

from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .field_class import FieldClass
    from .model import Model
    from .project import Project


class Field(Base):
    """Field model for classification dimensions.

    A Field represents one classification dimension (e.g., "Responsiveness", "Likeness").
    Each field can have multiple classes and its own trained model.
    """

    project_id: Mapped[str] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="fields")
    classes: Mapped[List["FieldClass"]] = relationship(
        back_populates="field",
        cascade="all, delete-orphan",
    )
    models: Mapped[List["Model"]] = relationship(
        back_populates="field",
        cascade="all, delete-orphan",
    )
