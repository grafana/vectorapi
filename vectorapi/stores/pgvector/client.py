# import asyncpg
from typing import List, Optional, Dict
import os 

from vectorapi.models.client import Client
from vectorapi.models.collection import Collection
from vectorapi.stores.pgvector.collection import PGVectorCollection, SCHEMA_NAME
from sqlalchemy.schema import CreateTable, DropTable

from sqlalchemy import MetaData
from sqlalchemy.sql import text
from sqlalchemy.schema import CreateSchema
from vectorapi.stores.pgvector.db import init_db_engine
from loguru import logger


class PGVectorClient(Client):
    def __init__(self):
        self.engine, self.bound_async_sessionmaker = init_db_engine()
        self._metadata = MetaData(schema=SCHEMA_NAME)

    async def init_db(self):
        await self.sync()
        async with self.engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.execute(CreateSchema(SCHEMA_NAME, if_not_exists=True))
            await conn.commit()

    async def sync(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(self._metadata.reflect)
            await conn.commit()

    async def create_collection(self, name: str, dimension: int) -> Collection:
        ## TODO: do the init bit during initialisation
        await self.init_db()
        logger.info(f"Creating collection with name {name}")
        col = PGVectorCollection(name=name, dimension=dimension)
        try:
            await col.create(session_maker=self.bound_async_sessionmaker, metadata=self._metadata)
        except Exception as e:
            logger.exception(e)
            raise e
        return col

    
    async def get_collection(self, name: str) -> Optional[Collection]:
        await self.sync()
        # table = self._metadata.tables.get(f"{self._metadata.schema}.{name}")
        ## How to get the dimension of the collection?
        table = self._metadata.tables.get(f"{SCHEMA_NAME}.{name}")
        if table is not None:
            logger.info(f"Found table: {table}")

        ##TODO: Need to get the dimension of the collection.
        ## Also there is no need to create a new collection here.
        c = PGVectorCollection(name=name, dimension=2)
        c._session_maker = self.bound_async_sessionmaker
        return c

    async def delete_collection(self, name: str):
        ## TODO: adopt a consistent implemetation with create_collection.
        await self.sync()
        try:
            table = self._metadata.tables.get(f"{self._metadata.schema}.{name}")
            if table is not None:
                logger.info(f"Found table: {table}")
                drop_expression = DropTable(table)
                logger.info(drop_expression)

                async with self.bound_async_sessionmaker() as session:
                    await session.execute(drop_expression)
                    await session.commit()
                self._metadata.remove(table)
            else:
                logger.info(f"Table {name} does not exist")
                raise ValueError(f"Table {name} does not exist")

        except Exception as e:
            logger.exception(e)
            raise e

    async def list_collections(self):
        await self.sync()
        return list(self._metadata.tables.keys())

    async def collection_exists(self, name: str) -> bool:
        await self.sync()
        return name in self._metadata.tables.keys()

# async def get_pgvector_client() -> Client:
#     """get_client returns the client instance."""
#     client = PGVectorClient()
#     await client.init_db()
#     return client
