# import asyncpg
from typing import List, Optional, Dict
import os

from vectorapi.models.client import Client
from vectorapi.models.collection import Collection
from vectorapi.stores.pgvector.collection import SCHEMA_NAME
from vectorapi.stores.pgvector.collection import PGVectorCollection
from sqlalchemy.schema import CreateTable, DropTable

from sqlalchemy import MetaData
from sqlalchemy.sql import text
from sqlalchemy.schema import CreateSchema
from vectorapi.stores.pgvector.db import init_db_engine
from loguru import logger
from vectorapi.stores.pgvector.base import Base


class PGVectorClient(Client):
    def __init__(self):
        self.engine, self.bound_async_sessionmaker = init_db_engine()
        self._metadata = Base.metadata

    async def setup(self):
        async with self.engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.execute(CreateSchema(SCHEMA_NAME, if_not_exists=True))
        await self.sync()

    async def sync(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(self._metadata.reflect)

    async def create_collection(self, name: str, dimension: int) -> Collection:
        ## TODO: do the init bit during initialisation
        logger.info(f"Creating collection name={name} dimension={dimension}")
        col = PGVectorCollection(
            name=name, dimension=dimension, session_maker=self.bound_async_sessionmaker
        )
        try:
            await col.create(session_maker=self.bound_async_sessionmaker, metadata=self._metadata)
        except Exception as e:
            logger.exception(e)
            raise e
        return col

    async def get_collection(self, name: str) -> Optional[Collection]:
        logger.info(f"Getting collection name={name}")
        # table = self._metadata.tables.get(f"{self._metadata.schema}.{name}")
        ## How to get the dimension of the collection?
        table = self._metadata.tables.get(f"{SCHEMA_NAME}.{name}")
        if table is not None:
            logger.info(f"Found table: {table}")
            # logger.info(table.__dict__)
            ##TODO: Need to get the dimension of the collection.
            ## Also there is no need to create a new collection here.
            collection = PGVectorCollection(
                name=name, dimension=2, session_maker=self.bound_async_sessionmaker
            )

            return collection
        return None

    async def delete_collection(self, name: str):
        logger.info(f"Deleting collection name={name}")
        ## TODO: adopt a consistent implemetation with create_collection.
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
        logger.info("Listing collections..")
        return [
            PGVectorCollection(
                name=table.name,
                dimension=2,
                session_maker=self.bound_async_sessionmaker,
            )
            for table in self._metadata.tables.values()
        ]

    async def collection_exists(self, name: str) -> bool:
        return name in self._metadata.tables.keys()


# async def get_pgvector_client() -> Client:
#     """get_client returns the client instance."""
#     client = PGVectorClient()
#     await client.init_db()
#     return client
