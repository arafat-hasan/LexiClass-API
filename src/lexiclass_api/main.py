"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from .api.v1.router import api_router
from .core.config import settings
from .core import storage  # Configure document storage at startup

# Disable synchronous event listeners from Core that don't work with async sessions
# The Core Document model has 'after_insert' and 'before_delete' listeners that are synchronous
# We need to handle document storage manually in the API service layer instead
from sqlalchemy import event
from lexiclass_core.models.document import Document as CoreDocument, store_document_after_insert, delete_document_before_delete

try:
    event.remove(CoreDocument, "after_insert", store_document_after_insert)
    event.remove(CoreDocument, "before_delete", delete_document_before_delete)
except Exception:
    pass  # Listeners might not be registered yet



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Setup
    logger = logging.getLogger(__name__)
    logger.info("Starting application")

    # Initialize database using Core's session factory
    from .db.session import initialize_database
    initialize_database()
    logger.info("Database initialized")

    yield
    # Cleanup
    logger.info("Shutting down application")


# Create FastAPI app
from .core.openapi import description, tags_metadata, contact, license_info, terms_of_service

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=description,
    version=settings.VERSION,
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    contact=contact,
    license_info=license_info,
    terms_of_service=terms_of_service,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Set up CORS
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Add API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.VERSION}


@app.get("/version")
async def version():
    """Version endpoint."""
    return {"version": settings.VERSION}
