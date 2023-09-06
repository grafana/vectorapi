import logging
from typing import Annotated, AsyncIterator

from fastapi import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from vectorapi.stores.pgvector.client_settings import settings
from typing import AsyncGenerator
from loguru import logger
from sqlalchemy.sql import text


def init_db_engine():
    async_engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URL.unicode_string(),
        pool_pre_ping=True,
        echo=settings.ECHO_SQL,
    )
    bound_async_sessionmaker = async_sessionmaker(
        bind=async_engine,
        autoflush=False,
        future=True,
    )
    # asyncio.run(async_engine.connect().execute(text("CREATE EXTENSION IF NOT EXISTS vector")))
    return (async_engine, bound_async_sessionmaker)
