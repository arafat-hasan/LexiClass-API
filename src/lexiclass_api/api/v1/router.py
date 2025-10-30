"""API v1 router."""

from fastapi import APIRouter

from . import documents, fields, indexing, prediction, projects, tasks, training

# Create API router
api_router = APIRouter()

# Include routers
# Note: Tags are specified in individual endpoint decorators for proper Swagger organization
api_router.include_router(projects.router, prefix="/projects")
api_router.include_router(documents.router, prefix="/projects")
api_router.include_router(indexing.router, prefix="/projects")
api_router.include_router(training.router, prefix="/projects")
api_router.include_router(prediction.router, prefix="/projects")
api_router.include_router(tasks.router)
api_router.include_router(fields.router)
