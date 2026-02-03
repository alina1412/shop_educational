import warnings
from typing import Any, AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

warnings.filterwarnings("ignore", category=DeprecationWarning)


from service.__main__ import app
from service.db_setup.db_settings import DbConnector, get_session


@pytest_asyncio.fixture(name="db", scope="function")
async def get_test_session() -> AsyncGenerator[sessionmaker, None]:
    async with DbConnector().session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            await session.close()


@pytest.fixture(name="client", scope="session")
def fixture_client() -> TestClient:  # type: ignore
    with TestClient(app) as client:
        yield client
