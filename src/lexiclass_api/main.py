"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from .api.v1.router import api_router
from .core.config import settings



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Setup
    logger = logging.getLogger(__name__)
    logger.info("Starting application")
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
