from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from service.config import logger
from service.db_accessors import CategoryAccessor, OrderProductAccessor
from service.db_setup.db_settings import get_session

api_router = APIRouter()


@api_router.get(
    "/statistic-order",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def show_statistic(db: AsyncSession = Depends(get_session)):
    """Get statistic"""

    category_manager = CategoryAccessor(db)
    result = await category_manager.get_category_by_id(id_=1)
    logger.debug("statistic-order")
    return {"data": "Success"}


@api_router.post(
    "/add-to-cart",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def add_to_order_cart(
    order_id: int,
    product_id: int,
    quantity: int,
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
