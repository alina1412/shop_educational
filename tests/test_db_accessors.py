import logging

from service.db_accessors import CategoryAccessor

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_db_create(db):
    try:
        category_manager = CategoryAccessor(db)
        result = await category_manager.create_category(
            {"title": "a", "parent_id": None}
        )
        logger.info(result)
    except Exception:
        await db.rollback()
        raise
