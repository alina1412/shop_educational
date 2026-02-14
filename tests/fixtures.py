from datetime import datetime, timedelta

import pytest_asyncio
import sqlalchemy

from service.db_setup.models import Category, Client, Order, OrderItem, Product


@pytest_asyncio.fixture(scope="function")
async def prepare_product_and_order(
    apply_migrations, test_session_factory
) -> None:
    session = test_session_factory()
    client = Client(
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
    await session.close()


@pytest_asyncio.fixture(scope="function")
async def prepare_subcategories(
    apply_migrations, test_session_factory
) -> None:
    """If not to run alembic data migrations automatically"""
    async with test_session_factory() as session:
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


@pytest_asyncio.fixture(scope="function")
async def prepare_orders_for_statistic(
    prepare_subcategories, test_session_factory
) -> None:
    async with test_session_factory() as session:
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
        order_old = Order(
            client_id=client.id, date=datetime.now() - timedelta(days=40)
        )
        product1 = Product(
            title="SmartphoneX",
            price=10.0,
            category_id=smatrphone_category_id,
            quantity=50,
        )
        product2 = Product(
            title="BookA",
            price=5.0,
            category_id=category_books_id,
            quantity=50,
        )
        session.add_all([product1, product2, order, order_old])
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

        order_item3 = OrderItem(
            order_id=order_old.id,
            product_id=product2.id,
            quantity=30,
            price_at_time=5.0,
        )
        session.add_all([order_item1, order_item2, order_item3])
        await session.commit()
