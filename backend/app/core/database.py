from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Module-level globals; initialised in lifespan
async_engine = None
AsyncSessionFactory: async_sessionmaker | None = None


async def init_db(database_url: str) -> None:
    global async_engine, AsyncSessionFactory
    async_engine = create_async_engine(
        database_url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )
    AsyncSessionFactory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if AsyncSessionFactory is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    async with AsyncSessionFactory() as session:
        yield session


async def close_db() -> None:
    global async_engine
    if async_engine is not None:
        await async_engine.dispose()
        async_engine = None
