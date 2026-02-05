import logging

from service.db_accessors import CategoryAccessor

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_db_create(apply_migrations, get_async_session):
    category_manager = CategoryAccessor(get_async_session)
    result = await category_manager.create_category(
        {"title": "a", "parent_id": None}
    )
    logger.info(result)
