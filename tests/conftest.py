import asyncio
from contextlib import asynccontextmanager
from urllib.parse import urlparse, urlunparse

import pytest
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from config import settings
from models.base import Base


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine(event_loop):
    # Attempt to create database if it doesn't exist
    parsed = urlparse(settings.TEST_DATABASE_URL)
    db_name = parsed.path.lstrip("/")
    base_url = urlunparse(parsed._replace(path="/postgres"))

    # Use NullPool to avoid loop-related issues with pooled connections
    temp_engine = create_async_engine(
        base_url, isolation_level="AUTOCOMMIT", poolclass=NullPool
    )
    async with temp_engine.connect() as conn:
        try:
            await conn.execute(sqlalchemy.text(f"CREATE DATABASE {db_name}"))
        except Exception:
            pass
    await temp_engine.dispose()

    engine = create_async_engine(
        settings.TEST_DATABASE_URL, echo=False, poolclass=NullPool
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_engine) -> AsyncSession:
    session_factory = async_sessionmaker(
        bind=test_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with session_factory() as session:
        yield session
        # Use rollback to ensure tests are isolated even if they commit
        await session.rollback()


@pytest.fixture(scope="function")
async def db_manager(db_session: AsyncSession):
    class MockDBManager:
        def __init__(self, session):
            self._session = session

        @asynccontextmanager
        async def session(self):
            yield self._session

    return MockDBManager(db_session)
