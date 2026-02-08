import asyncio
import warnings
from datetime import datetime
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
from service.db_setup.models import Category, Client, Order, OrderItem, Product

warnings.filterwarnings("ignore", category=DeprecationWarning)


TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"


@pytest.fixture(scope="session")
def apply_migrations():
    alembic_cfg = Config("alembic.ini")

    # Clean downgrade to base
    downgrade(alembic_cfg, "base")

    # Apply all migrations
    upgrade(alembic_cfg, "schema@head")
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


async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
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
        yield session

    await engine.dispose()


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
async def get_async_session_maker() -> async_sessionmaker[AsyncSession] | None:
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
    return session_maker


@pytest_asyncio.fixture(scope="session")
async def client():

    async def get_test_session():
        async for session in override_get_session():
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
    apply_migrations, get_async_session_maker
) -> None:
    async with get_async_session_maker() as session:
        client = Client(
            id=1,
            name="Test Client",
            email="test@example.com",
            address="Test Address",
        )
        category = Category(title="Test Category 1")

        session.add_all([category, client])
        await session.flush()

        order = Order(client_id=1)
        product = Product(
            title="Test Product 1", price=10.0, category_id=1, quantity=2
        )
        session.add_all([product, order])
        await session.flush()

        await session.commit()


@pytest_asyncio.fixture(scope="session")
async def prepare_subcategories(apply_migrations, get_async_session) -> None:
    """If not to run alembic data migrations automatically"""
    session = get_async_session

    category0 = Category(title="Electronics")

    session.add(category0)
    await session.flush()
    category_0_id = category0.id

    category1 = Category(title="Smartphones", parent_id=category_0_id)
    category2 = Category(title="Laptops", parent_id=category_0_id)
    session.add_all([category1, category2])
    await session.flush()
    category_1_id = category1.id
    category_2_id = category2.id

    category3 = Category(title="Android Phones", parent_id=category_1_id)
    category4 = Category(title="iPhones", parent_id=category_1_id)
    category5 = Category(title="Gaming Laptops", parent_id=category_2_id)

    session.add_all([category3, category4, category5])
    await session.commit()


@pytest_asyncio.fixture(scope="session")
async def prepare_orders_for_statistic(
    apply_migrations, prepare_subcategories, get_async_session
) -> None:
    session = get_async_session

    client = Client(
        name="Test Client",
        email="test@example.com",
        address="Test Address",
    )

    smatrphone_category_id = (
        await session.execute(
            sqlalchemy.select(Category.id).where(
                Category.title == "Smartphones"
            )
        )
    ).scalar_one()

    category0 = Category(title="Books")
    session.add(category0)
    await session.flush()
    category_books_id = category0.id

    session.add_all([client])
    await session.flush()

    order = Order(client_id=client.id, date=datetime.now())
    product1 = Product(
        title="SmartphoneX",
        price=10.0,
        category_id=smatrphone_category_id,
        quantity=5,
    )
    product2 = Product(
        title="BookA", price=5.0, category_id=category_books_id, quantity=5
    )
    session.add_all([product1, product2, order])
    await session.flush()

    order_item1 = OrderItem(
        order_id=order.id,
        product_id=product1.id,
        quantity=2,
        price_at_time=10.0,
    )
    order_item2 = OrderItem(
        order_id=order.id,
        product_id=product2.id,
        quantity=3,
        price_at_time=5.0,
    )
    session.add_all([order_item1, order_item2])
    await session.commit()
