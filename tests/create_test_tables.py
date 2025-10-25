"""Create tables in test database."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from lexiclass_api.models import Base, Project, Document, Task  # noqa: F401


async def create_tables():
    """Create all tables in test database."""
    engine = create_async_engine(
        'postgresql+asyncpg://lexiclass:lexiclass@localhost/lexiclass_test',
        echo=True
    )
    async with engine.begin() as conn:
        # Drop all tables first
        await conn.run_sync(Base.metadata.drop_all)
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print('\n✓ Test database tables created successfully')


if __name__ == "__main__":
    asyncio.run(create_tables())
