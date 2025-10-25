"""Models package - re-exports models from lexiclass_core.

All database models are now defined in lexiclass_core and re-exported here
for backward compatibility with existing API code.
"""

from lexiclass_core.models import (
    Base,
    Document,
    DocumentLabel,
    Field,
    FieldClass,
    IndexStatus,
    Model,
    ModelStatus,
    Prediction,
    Project,
)
from .task import Task

__all__ = [
    "Base",
    "Document",
    "DocumentLabel",
    "Field",
    "FieldClass",
    "IndexStatus",
    "Model",
    "ModelStatus",
    "Prediction",
    "Project",
    "Task",
]
