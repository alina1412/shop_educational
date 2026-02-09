import logging

from service.db_accessors import OrderClientAccessor

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_db_connect(apply_migrations, get_async_session):
    manager = OrderClientAccessor(get_async_session)
    _ = await manager.get_client(1)
    await get_async_session.aclose()
    logger.info("Database connection test passed")
