from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from service.config import logger
from service.db_setup.db_settings import db_connector
from service.endpoints.data_handlers import api_router as data_routes
from service.http_exceptions import add_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    yield
    logger.warning("Shutting down...")
    await db_connector.dispose_engine()


app = FastAPI(lifespan=lifespan)

app = add_exception_handlers(app)

app.include_router(data_routes)


if __name__ == "__main__":
    uvicorn.run("service.__main__:app", host="0.0.0.0", port=8000, reload=True)
