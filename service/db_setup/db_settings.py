from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from service.config import db_settings, logger


class DbConnector:
    def __init__(self) -> None:
        self.engine: AsyncEngine | None = None
        self._session_maker: async_sessionmaker | None = None

    @property
    def uri(self) -> str:
        return (
            f"{db_settings['db_driver']}"
            "://"
            f"{db_settings['db_user']}:{db_settings['db_password']}"
            f"@{db_settings['db_host']}:{db_settings['db_port']}"
            f"/{db_settings['db_name']}"
        )

    def get_engine(self) -> AsyncEngine:
        self.engine = create_async_engine(
            self.uri,
            pool_size=1,
            max_overflow=0,
            pool_recycle=280,
            pool_timeout=20,
            echo=True,
            future=True,
        )
        return self.engine

    @property
    def session_maker(self) -> async_sessionmaker:
        if not self.engine:
            self.get_engine()
        return async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def dispose_engine(self):
        """Dispose engine when application shuts down"""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self._session_maker = None


db_connector = DbConnector()


async def get_session() -> AsyncGenerator:
    session = db_connector.session_maker()
    try:
        yield session
        await session.commit()
    except Exception as exc:
        logger.error("Error in session", exc_info=exc)
        await session.rollback()
        raise exc
    finally:
        await session.close()
