import logging
import time
from contextlib import contextmanager

import sqlalchemy as sa

from service.db_accessors import OrderClientAccessor, StatisticAccessor
from service.db_setup.models import Category, Product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


async def test_db_connect(apply_migrations, get_async_session):
    manager = OrderClientAccessor(get_async_session)
    _ = await manager.get_client(1)
    await get_async_session.aclose()
    logger.info("Database connection test passed")


@contextmanager
def timer():
    """Context manager to measure execution time."""
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    logger.info(f"xxxxxx--- Execution time: {elapsed:.4f} seconds ---xxxxxx")


async def test_run_sql(
    apply_migrations, prepare_orders_for_statistic, get_async_session_maker
):

    async def create_many_subcategories(session, num, parent_id=None):
        title = "top_parent" if not parent_id else str(num)
        category = Category(title=title, parent_id=parent_id)
        session.add(category)
        await session.flush()
        return category.id

    async with get_async_session_maker() as session:
        id_ = None
        for i in range(40):
            id_ = await create_many_subcategories(session, i, parent_id=id_)

        product = (
            await session.execute(sa.select(Product).where(Product.id == 1))
        ).scalar_one_or_none()
        product.category_id = id_
        await session.commit()

        with timer():
            results = await StatisticAccessor(
                session
            ).get_top_selling_products()

        logger.info(f"{results}")
        assert results == [
            {
                "product_title": "BookA",
                "top_parent_title": "Books",
                "total_quantity": 3,
            },
            {
                "product_title": "SmartphoneX",
                "top_parent_title": "top_parent",
                "total_quantity": 2,
            },
        ]

        for child_id, top_parent_id, _ in results:
            logger.info(f"Category {child_id} -> Top Parent: {top_parent_id}")
