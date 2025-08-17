"""Indexing tasks."""

import logging
from typing import List

from celery import Task

from ..db.session import async_session
from ..models.document import Document
from ..services.documents import DocumentService
from ..worker import celery_app

logger = logging.getLogger(__name__)


class IndexingTask(Task):
    """Base task for indexing operations."""

    _service = None

    @property
    def service(self) -> DocumentService:
        """Get document service.

        Returns:
            Document service instance
        """
        if self._service is None:
            self._service = DocumentService(async_session())
        return self._service


@celery_app.task(base=IndexingTask, bind=True)
async def index_documents(
    self, project_id: str, document_ids: List[str] | None = None, is_incremental: bool = True
) -> dict:
    """Index documents in a project.

    Args:
        project_id: Project ID
        document_ids: Optional list of document IDs to index
        is_incremental: Whether to perform incremental indexing

    Returns:
        Task result with indexing statistics
    """
    try:
        # Get documents to index
        if document_ids:
            # Index specific documents
            documents = await self.service.get_multi_by_ids(project_id, document_ids)
        else:
            # Index all documents or only unindexed ones
            status = "pending" if is_incremental else None
            documents = await self.service.get_multi(project_id, status=status)

        if not documents:
            return {"indexed": 0, "status": "completed", "message": "No documents to index"}

        # Update document status
        for doc in documents:
            doc.status = "indexing"
        await self.service.db.commit()

        try:
            # TODO: Implement actual indexing logic here
            # This would typically involve:
            # 1. Text preprocessing
            # 2. Feature extraction
            # 3. Index updates
            # 4. Embeddings calculation
            # For now, we'll just simulate indexing
            
            # Mark documents as indexed
            for doc in documents:
                doc.status = "indexed"
            await self.service.db.commit()

            return {
                "indexed": len(documents),
                "status": "completed",
                "message": "Documents indexed successfully",
            }

        except Exception as e:
            # Mark documents as failed
            for doc in documents:
                doc.status = "failed"
            await self.service.db.commit()
            
            raise e

    except Exception as e:
        logger.exception("Indexing failed")
        return {
            "indexed": 0,
            "status": "failed",
            "message": str(e),
        }
    finally:
        await self.service.db.close()
