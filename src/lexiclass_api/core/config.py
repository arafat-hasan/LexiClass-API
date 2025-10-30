"""Configuration settings for the API service."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import (
    PostgresDsn,
    RedisDsn,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """API service settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "LexiClass API"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "API service for document classification"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    PORT: int = 8000

    # CORS Settings
    CORS_ORIGINS_STR: str = "http://localhost:3000,http://localhost:8000"
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Get list of CORS origins."""
        return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",") if origin.strip()]

    # Database
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URI: Optional[PostgresDsn] = None

    @field_validator("DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_uri(
        cls, v: Optional[str], values: Dict[str, Any]
    ) -> PostgresDsn:
        """Construct database URI from components."""
        if isinstance(v, str):
            return PostgresDsn(v)

        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.data["POSTGRES_USER"],
            password=values.data["POSTGRES_PASSWORD"],
            host=values.data["POSTGRES_HOST"],
            port=int(values.data["POSTGRES_PORT"]),
            path=values.data["POSTGRES_DB"],
        )

    # Redis and Celery
    REDIS_HOST: str
    REDIS_PORT: str
    REDIS_PASSWORD: Optional[str] = None
    CELERY_BROKER_URL: Optional[RedisDsn] = None
    CELERY_RESULT_BACKEND: Optional[RedisDsn] = None
    
    # Celery Settings
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_ENABLE_UTC: bool = True
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_RETRY_BACKOFF: bool = True
    CELERY_TASK_RETRY_JITTER: bool = True
    CELERY_TASK_DEFAULT_RATE_LIMIT: str = "100/m"
    CELERY_TASK_DEFAULT_RETRY_DELAY: int = 3
    CELERY_TASK_MAX_RETRIES: int = 3
    CELERY_TASK_SOFT_TIME_LIMIT: int = 600
    CELERY_TASK_TIME_LIMIT: int = 1200
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 4
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 1000
    CELERY_WORKER_SEND_TASK_EVENTS: bool = True

    @field_validator("CELERY_BROKER_URL", "CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def assemble_redis_uri(
        cls, v: Optional[str], values: Dict[str, Any]
    ) -> RedisDsn:
        """Construct Redis URI from components."""
        if isinstance(v, str):
            return RedisDsn(v)

        return RedisDsn.build(
            scheme="redis",
            host=values.data["REDIS_HOST"],
            port=int(values.data["REDIS_PORT"]),
            password=values.data.get("REDIS_PASSWORD"),
        )

    # Storage
    STORAGE_PATH: Path = Path("/data")

    def get_project_storage_path(self, project_id: int) -> Path:
        """Get the base storage path for a project.

        Args:
            project_id: Project ID

        Returns:
            Path to project storage directory
        """
        return self.STORAGE_PATH / f"{project_id}"

    def get_models_path(self, project_id: int) -> Path:
        """Get the models path for a project.

        Args:
            project_id: Project ID

        Returns:
            Path to project models directory
        """
        return self.get_project_storage_path(project_id) / "models"

    def get_indexes_path(self, project_id: int) -> Path:
        """Get the indexes path for a project.

        Args:
            project_id: Project ID

        Returns:
            Path to project indexes directory
        """
        return self.get_project_storage_path(project_id) / "indexes"

    def get_documents_path(self, project_id: int) -> Path:
        """Get the documents path for a project.

        Args:
            project_id: Project ID

        Returns:
            Path to project documents directory
        """
        return self.get_project_storage_path(project_id) / "documents"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOGGING_CONFIG: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(timestamp)s %(level)s %(name)s %(message)s",
            },
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
    }





settings = Settings()  # type: ignore
