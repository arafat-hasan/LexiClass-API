"""Database session management - uses Core's session factory."""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from lexiclass_core.db.session import get_db_session, init_db

from ..core.config import settings


def initialize_database() -> None:
    """Initialize database connection using Core's session factory."""
    init_db(str(settings.DATABASE_URI))


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    """Dependency for database session.

    Uses the shared database session from lexiclass_core.
    """
    async with get_db_session() as session:
        yield session
