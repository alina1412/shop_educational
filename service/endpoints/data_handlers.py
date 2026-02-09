from typing import List, Tuple

from fastapi import APIRouter, Depends, status
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession

from service.config import logger
from service.db_accessors import (
    OrderProductAccessor,
    StatisticAccessor,
)
from service.db_setup.db_settings import get_session
from service.schemas import ClientOrderSum, SubcategoryCount, TopProducts

api_router = APIRouter()


@api_router.get(
    "/client-order-sum",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
    response_model=List[ClientOrderSum],
)
async def show_client_orders_sum(db: AsyncSession = Depends(get_session)):
    """Покажет список [имя клиента, сумма стоимости товаров],
    если в заказе нет товаров, то сумма будет 0,
    если у клиента нет заказов, то он не будет в списке.
    """
    result = await StatisticAccessor(db).get_client_orders_sum()
    return [
        ClientOrderSum(name=row.name, total_sum=row.total_sum)
        for row in result
    ]


@api_router.get(
    "/count-subcategories",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def count_subcategories(db: AsyncSession = Depends(get_session)):
    """Количество подкатегорий первого уровня вложенности
    для каждой категории."""
    categories = await StatisticAccessor(db).get_count_subcategories()
    return [SubcategoryCount(**dict(row)) for row in categories]


@api_router.get(
    "/statistic-order",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
    response_model=list[TopProducts],
)
async def show_statistic(db: AsyncSession = Depends(get_session)):
    """Get statistic
    Топ 5 количества проданных товаров за последний месяц,
    Наименование товара, Категория верхнего уровня,
    Общее количество проданных штук.
    """

    result = await StatisticAccessor(db).get_top_selling_products()

    return [
        TopProducts(
            product_name=row.product_title,
            category_name=row.category_top_title or row.category_title,
            total_quantity=row.total_quantity,
        )
        for row in result
    ]


@api_router.post(
    "/add-to-cart",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def add_to_order_cart(
    order_id: int = Query(..., gt=0),
    product_id: int = Query(..., gt=0),
    quantity: int = Query(..., gt=0),
    session: AsyncSession = Depends(get_session),
):
    """Add to order cart some product"""
    logger.debug(
        f"order_id={order_id}, product_id={product_id}, quantity={quantity}"
    )

    order_product_accessor = OrderProductAccessor(session)
    await order_product_accessor.add_product_to_order(
        order_id, product_id, quantity
    )

    return {"data": "Success"}
