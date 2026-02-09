from datetime import datetime, timedelta
from typing import Optional

import pytz
from sqlalchemy import Integer, func, join, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from service.config import logger
from service.db_setup.models import (
    Category,
    Client,
    Order,
    OrderItem,
    Product,
)
from service.exceptions import (
    ClientNotFound,
    OrderNotFound,
    ProductNotAvailable,
    ProductNotFound,
)


class DbAccessor:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.local_tz = pytz.timezone("UTC")


class OrderClientAccessor(DbAccessor):
    async def create_new_order(self, client_id: int) -> int | None:
        if not await self.get_client(client_id):
            logger.info(
                f"Client {client_id} not found when creating new order"
            )
            raise ClientNotFound(f"Client {client_id} not found")

        stmt = insert(Order).values(client_id=client_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return (
            result.inserted_primary_key[0]
            if result.inserted_primary_key
            else None
        )

    async def get_client(self, client_id: int) -> Optional[Client]:
        return await self.session.get(Client, client_id)


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


class StatisticAccessor(DbAccessor):
    async def get_client_orders_sum(self):
        query = (
            select(
                Client.name,
                func.coalesce(
                    func.sum(OrderItem.quantity * OrderItem.price_at_time), 0
                ).label("total_sum"),
            )
            .join(
                Order, Client.id == Order.client_id
            )  # INNER JOIN - only clients with orders
            .outerjoin(
                OrderItem, Order.id == OrderItem.order_id
            )  # LEFT JOIN - orders may have no items
            .group_by(Client.id, Client.name)
        )
        result = await self.session.execute(query)
        return result.all()

    async def get_count_subcategories(self):
        subcategories = aliased(Category)

        query = (
            select(
                Category.title,
                func.count(subcategories.id).label("subcategories_count"),
            )
            .outerjoin(subcategories, subcategories.parent_id == Category.id)
            .group_by(Category.id, Category.title)
            .order_by(Category.id)
        )
        result = await self.session.execute(query)
        return result.mappings().all()

    async def get_top_selling_products(self):
        MONTH_AGO = datetime.now(self.local_tz) - timedelta(days=30)
        parent = aliased(Category, name="parent")

        cte = select(
            Category.id.label("child_id"),
            Category.id.label("parent_id"),
            Category.parent_id.label("immediate_parent_id"),
            func.cast(0, Integer).label("level"),
        ).cte(name="category_hierarchy", recursive=True)

        recursive_part = (
            select(
                cte.c.child_id.label("child_id"),
                parent.id.label("parent_id"),
                parent.parent_id.label("immediate_parent_id"),
                (cte.c.level + 1).label("level"),
            )
            .select_from(cte)
            .join(parent, cte.c.immediate_parent_id == parent.id)
            .where(cte.c.immediate_parent_id.isnot(None))
        )

        category_hierarchy = cte.union_all(recursive_part)

        cat_parent = aliased(Category, name="cat_parent")

        main_query = (
            select(
                Product.title.label("product_title"),
                cat_parent.title.label("top_parent_title"),
                func.sum(OrderItem.quantity).label("total_quantity"),
            )
            .select_from(category_hierarchy)
            .join(
                Product, Product.category_id == category_hierarchy.c.child_id
            )
            .join(cat_parent, cat_parent.id == category_hierarchy.c.parent_id)
            .join(OrderItem, OrderItem.product_id == Product.id)
            .join(Order, OrderItem.order_id == Order.id)
            .where(
                category_hierarchy.c.immediate_parent_id.is_(None),
                Order.date >= MONTH_AGO,
            )
            .group_by(
                Product.title,
                cat_parent.title,
            )
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(5)
        )

        result = (await self.session.execute(main_query)).mappings().all()
        return result
