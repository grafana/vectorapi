# import asyncpg
from typing import List, Optional

from vectorapi.models.client import Client
from vectorapi.models.collection import Collection
from vectorapi.stores.pgvector.client_settings import Settings
from vectorapi.stores.pgvector.collection import PGVectorCollection
from sqlalchemy.schema import CreateTable

from sqlalchemy import Table, Column, String, MetaData
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text
from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from vectorapi.stores.pgvector.db import get_session
from loguru import logger


class PGVectorClient(Client):
    def __init__(self, session: AsyncSession = get_session):
        self.async_session = session

        # self.engine = create_async_engine(str(settings.SQLALCHEMY_DATABASE_URL), echo=True, future=True)
        # self.async_session = async_sessionmaker(
        #         self.engine,
        #         expire_on_commit=False,
        #     )

    async def create_collection(self, name: str, dimension: int) -> Collection:
        logger.info(f"Creating collection with name {name}")
        meta = MetaData()
        collection = Table(
            name,
            meta,
        Column("id", String, primary_key=True),
        Column("embeddings", Vector(dimension), nullable=False),
        Column(
            "metadata",
            postgresql.JSONB,
            server_default=text("'{}'::jsonb"),
            nullable=False,
        ),
        extend_existing=True,
        )
        create_expression = CreateTable(collection)
        logger.info(create_expression)

        try:
            await self.async_session().execute(create_expression)
        except Exception as e:
            logger.exception(e)
            raise e
        return PGVectorCollection(name=name, dimension=dimension, table=collection)
        
        #     # async with self.engine.begin() as conn:
        # async with self.async_session.begin() as session:
        #     session.scalar()
            # await conn.run_sync(meta.drop_all)
            # await conn.run_sync(meta.create_all)

    
    async def get_collection(self, name: str) -> Optional[Collection]:
        async with self.engine.begin() as conn:
            conn.execute(f"SELECT * FROM {name}")
            pass

    async def delete_collection(self, name: str):
        async with self.engine.begin() as conn:
            pass

    async def list_collections(self) -> List[Collection]:
        async with self.engine.begin() as conn:
            pass


def get_pgvector_client() -> Client:
    """get_client returns the client instance."""
    return PGVectorClient(session=AsyncSession)
