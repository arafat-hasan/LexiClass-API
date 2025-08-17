"""Dependencies for FastAPI application."""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_db as get_db_session


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    """Get database session."""
    async for session in get_db_session():
        yield session