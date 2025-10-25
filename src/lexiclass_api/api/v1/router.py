"""API v1 router."""

from fastapi import APIRouter

from . import documents, fields, indexing, prediction, projects, tasks, training

# Create API router
api_router = APIRouter()

# Include routers
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(documents.router, prefix="/projects", tags=["documents"])
api_router.include_router(indexing.router, prefix="/projects", tags=["indexing"])
api_router.include_router(training.router, prefix="/projects", tags=["training"])
api_router.include_router(prediction.router, prefix="/projects", tags=["prediction"])
api_router.include_router(tasks.router, tags=["tasks"])
api_router.include_router(fields.router, tags=["fields", "field-classes", "document-labels"])
