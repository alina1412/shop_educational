from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from service.config import logger
from service.db_accessors import CategoryAccessor
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
async def add_to_order(
    add_data=None, session: AsyncSession = Depends(get_session)
):
    """Add to order cart some product"""

    try:
        1 == 2
        # await add_some_data(session, {"id": 2})
    except Exception as exc:
        logger.debug("NOT_FOUND")
        raise HTTPException(status.HTTP_404_NOT_FOUND, "NOT_FOUND") from exc

    return {"data": "Success"}
