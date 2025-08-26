"""Document storage utilities."""

import os
from pathlib import Path
from typing import Optional

from .config import settings


class DocumentStorage:
    """Handle document storage operations."""

    def __init__(self) -> None:
        """Initialize document storage."""
        self.base_path = settings.STORAGE_PATH / settings.DOCUMENTS_DIR
        self._ensure_storage_path()

    def _ensure_storage_path(self) -> None:
        """Ensure the storage directory exists."""
        os.makedirs(self.base_path, exist_ok=True)

    def _get_project_path(self, project_id: str) -> Path:
        """Get project directory path."""
        project_path = self.base_path / project_id
        os.makedirs(project_path, exist_ok=True)
        return project_path

    def get_document_path(self, project_id: str, document_id: str) -> Path:
        """Get the full path for a document."""
        return self._get_project_path(project_id) / f"{document_id}.txt"

    def store_document(self, project_id: str, document_id: str, content: str) -> Path:
        """Store document content and return the file path."""
        file_path = self.get_document_path(project_id, document_id)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path

    def read_document(self, project_id: str, document_id: str) -> Optional[str]:
        """Read document content from storage."""
        file_path = self.get_document_path(project_id, document_id)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return None

    def delete_document(self, project_id: str, document_id: str) -> bool:
        """Delete a document from storage."""
        file_path = self.get_document_path(project_id, document_id)
        try:
            os.remove(file_path)
            return True
        except FileNotFoundError:
            return False


# Create a singleton instance
document_storage = DocumentStorage()
