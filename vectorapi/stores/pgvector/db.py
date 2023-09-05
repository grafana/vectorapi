import logging
from typing import Annotated, AsyncIterator

from fastapi import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from vectorapi.stores.pgvector.client_settings import settings
from typing import AsyncGenerator
from loguru import logger


async_engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URL.unicode_string(),
    pool_pre_ping=True,
    echo=settings.ECHO_SQL,
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    future=True,
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# AsyncSession = Annotated[async_sessionmaker, Depends(get_session)]
