from fastapi import FastAPI, HTTPException, status

from service.exceptions import (
    OrderNotFound,
    ProductNotAvailable,
    ProductNotFound,
)


class ProductNotFoundHttpException(HTTPException):
    def __init__(self, product_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )


def add_exception_handlers(app: FastAPI):

    @app.exception_handler(ProductNotFound)
    async def product_not_found_handler(request, exc):
        raise HTTPException(status_code=404, detail=str(exc))

    @app.exception_handler(OrderNotFound)
    async def order_not_found_handler(request, exc):
        raise HTTPException(status_code=404, detail=str(exc))

    @app.exception_handler(ProductNotAvailable)
    async def product_not_available_handler(request, exc):
        raise HTTPException(status_code=400, detail=str(exc))

    return app
