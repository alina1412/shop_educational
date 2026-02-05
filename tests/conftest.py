import asyncio
import warnings
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)


warnings.filterwarnings("ignore", category=DeprecationWarning)


from service.__main__ import app
from service.db_setup.db_settings import get_session

TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"


# @pytest.fixture(scope="session", autouse=True)
# def event_loop():
#     """Session-scoped event loop fixture"""
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     yield loop
#     loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(
        TEST_DB_URL,
        echo=False,
        poolclass=None,
    )

    yield engine

    await engine.dispose()


async def override_get_session(engine) -> AsyncGenerator[AsyncSession, None]:
    session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
async def get_async_session(engine) -> AsyncSession | None:

    async for session in override_get_session(engine):
        return session  # returns one


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
