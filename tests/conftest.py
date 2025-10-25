"""Test configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from lexiclass_api.core.config import settings
from lexiclass_api.core.deps import get_db
from lexiclass_api.models.base import Base
from lexiclass_api.main import app

# Import all models so Base.metadata knows about them
from lexiclass_api.models import Project, Document, Task  # noqa: F401


# Use a separate test database
# Replace only the database name in the path, not in the user
TEST_DATABASE_URL = str(settings.DATABASE_URI).rsplit("/", 1)[0] + "/lexiclass_test"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    print(f"\n✓ Test database initialized with tables: {[t.name for t in Base.metadata.sorted_tables]}")

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="session")
async def test_session_factory(test_engine):
    """Create a session factory for tests."""
    return sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture
async def db_session(test_session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for a test.

    Each test gets a fresh session. Data persists during the test
    and is cleaned up at the end.
    """
    async with test_session_factory() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()


@pytest.fixture
async def client(test_session_factory) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing.

    Overrides the database dependency to create a new session for each request,
    which better simulates real API behavior.
    """

    async def override_get_db():
        async with test_session_factory() as session:
            try:
                yield session
                # Ensure commit happens after service operations
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Content-Type": "application/json"}
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()

    # Cleanup: delete all data after test
    async with test_session_factory() as cleanup_session:
        async with cleanup_session.begin():
            for table in reversed(Base.metadata.sorted_tables):
                await cleanup_session.execute(table.delete())
        await cleanup_session.commit()


@pytest.fixture
def api_url() -> str:
    """Get the API base URL."""
    return settings.API_V1_STR
