import asyncio
import warnings
from typing import AsyncGenerator

import pytest
import pytest_asyncio
import sqlalchemy
from alembic.command import downgrade, upgrade
from alembic.config import Config
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from service.__main__ import app
from service.db_setup.db_settings import get_session
from service.db_setup.models import Category, Client, Order, Product

warnings.filterwarnings("ignore", category=DeprecationWarning)


TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"


@pytest.fixture(scope="session")
def apply_migrations():
    alembic_cfg = Config("alembic.ini")

    # Clean downgrade to base
    downgrade(alembic_cfg, "base")

    # Apply all migrations
    upgrade(alembic_cfg, "head")

    yield
    # Optional: cleanup after tests
    # downgrade(alembic_cfg, "base")


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
async def get_async_session() -> AsyncSession | None:
    engine = create_async_engine(
        TEST_DB_URL,
        echo=False,
        poolclass=None,
    )
    session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_maker() as session:
        return session
    # async for session in override_get_session(engine):
    #     return session  # returns one


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


@pytest_asyncio.fixture(scope="session")
async def prepare_product_and_order(
    apply_migrations, get_async_session
) -> None:
    session = get_async_session
    # User.objects.create(id=1, username="testuser", password="testpass")
    # try:
    client = Client(
        id=1,
        name="Test Client",
        email="test@example.com",
        address="Test Address",
    )
    category = Category(title="Test Category 1")
    # session.add(user)
    session.add_all([category, client])
    await session.flush()

    # Category.objects.create(id=1, title="Test Category 1")
    # Order.objects.create(id=1, user_id=1)
    # Product.objects.create(title="Test Product 1", price=10.0, category_id=1)
    order = Order(client_id=1)
    product = Product(title="Test Product 1", price=10.0, category_id=1)
    session.add_all([product, order])
    await session.flush()

    await session.commit()

    # except sqlalchemy.exc.IntegrityError:
    #     await session.rollback()
