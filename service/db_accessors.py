import sqlalchemy as sa
from sqlalchemy import delete, or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from service.config import logger
from service.db_setup.models import Category, User
from service.exceptions import OrderNotFound, ProductNotFound


class DbAccessor:
    def __init__(self, session: AsyncSession):
        self.session = session


class UserAccessor(DbAccessor):
    async def get_user_by_id(self, id_: int) -> User | None:
        return await self.session.get(User, id_)


class CategoryAccessor(DbAccessor):
    async def create_category(self, vals: dict) -> int | None:
        try:
            category = Category(**vals)
            self.session.add(category)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(category)
        except sa.exc.IntegrityError as exc:
            logger.error("Error adding category: ", exc_info=exc)
            await self.session.rollback()
            return None
        logger.info("added category %s", category.id)
        return category.id

    async def get_category_by_id(self, id_: int) -> Category | None:
        return await self.session.get(Category, id_)
        import sqlalchemy as sa

        query = sa.select(Category)
        result = await self.session.execute(query)
        return result.scalars().all()
        # engine = self.session
        # async with engine.connect() as conn:
        #     res = await conn.execute(text("SELECT 1"))
        # q = select(Category).where(Category.id == 1)
        # result = await self.session.execute(q)
        # res = result.scalars().all()
        return res

    def filter_edited_vals(self, edited_vals: dict) -> dict:
        PASWD_MIN_LEN = 3
        category_edit_fields = ("categoryname", "password")
        not_empty_vals = {
            key: val
            for key, val in edited_vals.items()
            if val is not None
            and key in category_edit_fields
            and (len(val) >= PASWD_MIN_LEN if key == "password" else True)
        }
        return not_empty_vals

    async def patch_category_by_id(
        self, id_: int, edited_vals: dict
    ) -> Category | None:
        new_vals = self.filter_edited_vals(edited_vals)
        if not new_vals:
            return None
        query_result = await self.session.get(Category, id_)
        if not query_result:
            return None
        try:
            for key, value in new_vals.items():
                setattr(query_result, key, value)
            await self.session.flush()
            await self.session.commit()
        except sa.exc.IntegrityError as exc:
            logger.error("Error paching category: ", exc_info=exc)
            await self.session.rollback()
            return None
        return query_result

    async def delete_category(self, id_: int) -> bool:
        query = sa.delete(Category).where(Category.id == id_)
        result = await self.session.execute(query)
        await self.session.commit()
        return bool(result.rowcount)


class OrderProductAccessor(DbAccessor):
    async def check_if_product_available(
        self, product_id: int, quantity: int
    ) -> bool:
        return product_id != 9999

    async def check_if_order_exists(self, order_id: int) -> bool:
        return order_id != 9999

    async def add_product_to_order(
        self, order_id: int, product_id: int, quantity: int
    ) -> None:
        if not await self.check_if_order_exists(order_id):
            raise OrderNotFound()
        if not await self.check_if_product_available(product_id, quantity):
            raise ProductNotFound()
