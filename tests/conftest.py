import asyncio
import warnings
from typing import Any, AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

warnings.filterwarnings("ignore", category=DeprecationWarning)


from service.__main__ import app
from service.db_setup.db_settings import DbConnector, get_session
from service.db_setup.models import Base

TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"


# @pytest.fixture(scope="session", autouse=True)
# def event_loop():
#     """Session-scoped event loop fixture"""
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     yield loop
#     loop.close()


from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(
        TEST_DB_URL,
        echo=False,
        poolclass=None,
    )

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db(engine):
    """Provide a database session for each test"""
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_session_override():
    engine = create_async_engine(url=TEST_DB_URL)

    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

    # Properly dispose of the engine after session is done
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def client():
    app.dependency_overrides[get_session] = get_session_override

    async with AsyncClient(
        transport=ASGITransport(app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()
