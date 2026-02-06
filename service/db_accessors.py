from datetime import datetime
from typing import Optional

import pytz
import sqlalchemy as sa
from sqlalchemy import delete, func, or_, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from service.config import logger
from service.db_setup.models import Category, Order, OrderItem, Product, User
from service.exceptions import (
    OrderNotFound,
    ProductNotAvailable,
    ProductNotFound,
)


class DbAccessor:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.local_tz = pytz.timezone("UTC")


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
    async def add_product_to_order(
        self, order_id: int, product_id: int, quantity: int
    ) -> None:
        # try:
        await self._add_product_to_order(order_id, product_id, quantity)
        # except SQLAlchemyError as e:
        #     # Database errors
        #     logger.error(f"Database error in upsert_order_item: {e}")
        #     raise

    async def _add_product_to_order(
        self, order_id: int, product_id: int, quantity: int
    ) -> None:
        current_session = self.session

        async with current_session.begin():
            order = await self._get_order_with_lock(order_id, current_session)
            if not order:
                raise OrderNotFound(f"Order {order_id} not found")

            order.date = datetime.now(self.local_tz)

            product = await self._get_product_with_lock(
                product_id, current_session
            )
            if not product:
                raise ProductNotFound(f"Product {product_id} not found")

            if product.quantity < quantity:
                raise ProductNotAvailable(
                    f"Insufficient stock. Available: {product.quantity}"
                )

            product.quantity -= quantity

            await self._upsert_order_item(
                order_id, product_id, quantity, product.price
            )

    async def _get_order_with_lock(
        self, order_id: int, current_session
    ) -> Optional[Order]:
        stmt = select(Order).where(Order.id == order_id).with_for_update()
        result = await current_session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_product_with_lock(
        self, product_id: int, current_session
    ) -> Optional[Product]:
        stmt = (
            select(Product).where(Product.id == product_id).with_for_update()
        )
        result = await current_session.execute(stmt)
        return result.scalar_one_or_none()

    async def _upsert_order_item(
        self,
        order_id: int,
        product_id: int,
        quantity: int,
        price: float,
    ):
        stmt = insert(OrderItem).values(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            price_at_time=price,
        )

        stmt = stmt.on_conflict_do_update(
            constraint="uq_order_product",
            set_={
                "quantity": OrderItem.quantity + quantity,
            },
        )

        await self.session.execute(stmt)
