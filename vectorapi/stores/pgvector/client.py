# import asyncpg
from typing import List, Optional, Dict

from vectorapi.models.client import Client
from vectorapi.models.collection import Collection
from vectorapi.stores.pgvector.client_settings import Settings
from vectorapi.stores.pgvector.collection import PGVectorCollection
from sqlalchemy.schema import CreateTable, DropTable

from sqlalchemy import Table, Column, String, MetaData
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text
from vectorapi.stores.pgvector.db import init_db_engine
from loguru import logger

class PGVectorClient(Client):
    def __init__(self):
        self.engine, self.bound_async_sessionmaker = init_db_engine()
        self.collections = MetaData()
        self._collections_list: List[Dict[str, PGVectorCollection]] = []

    async def init_db(self):
        await self.sync()
        async with self.engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.commit()

    async def sync(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(self.collections.reflect)
            await conn.commit()

    async def create_collection(self, name: str, dimension: int) -> Collection:
        ## TODO: do the init bit during initialisation
        await self.init_db()
        logger.info(f"Creating collection with name {name}")
        collection = Table(
            name,
            self.collections,
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
        col = PGVectorCollection(name=name, dimension=dimension)
        
        try:
            async with self.bound_async_sessionmaker() as session:
                await session.execute(create_expression)
                await session.commit()
        except Exception as e:
            logger.exception(e)
            raise e
        return col

    
    async def get_collection(self, name: str) -> Optional[Collection]:
        async with self.bound_async_sessionmaker() as session:
            await session.execute(text(f"SELECT * FROM {name}"))
            await session.commit()
            

    async def delete_collection(self, name: str):
        await self.sync()
        try:
            table = self.collections.tables.get(name)
            if table is not None:
                logger.info(f"Found table: {table}")
                drop_expression = DropTable(table)
                logger.info(drop_expression)

                async with self.bound_async_sessionmaker() as session:
                    await session.execute(drop_expression)
                    await session.commit()
            else:
                logger.info(f"Table {name} does not exist")
                raise ValueError(f"Table {name} does not exist")

        except Exception as e:
            logger.exception(e)
            raise e

    async def list_collections(self):
        await self.sync()
        return list(self.collections.tables.keys())


# async def get_pgvector_client() -> Client:
#     """get_client returns the client instance."""
#     client = PGVectorClient()
#     await client.init_db()
#     return client
