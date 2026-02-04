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


async def override_get_session(engine) -> AsyncGenerator[AsyncSession, None]:
    async with async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )() as session:
        try:
            yield session
        except Exception as exc:
            await session.rollback()
            raise exc
        finally:
            await session.close()
            if engine:
                await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def get_async_session(engine):
    async for session in override_get_session(engine):
        yield session


@pytest_asyncio.fixture(scope="session")
async def client(engine):
    async def get_test_session():
        async for session in override_get_session(engine):
            return session

    # app.dependency_overrides[get_session] = lambda: get_test_session(engine)
    app.dependency_overrides[get_session] = get_test_session

    async with AsyncClient(
        transport=ASGITransport(app),
        base_url="http://test",
    ) as client:
        yield client

    # with TestClient(app) as client:
    #     yield client

    app.dependency_overrides.clear()
