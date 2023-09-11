# import asyncpg
from typing import List, Optional, Dict
import os

from vectorapi.models.client import Client
from vectorapi.models.collection import Collection
from vectorapi.stores.pgvector.collection import SCHEMA_NAME
from vectorapi.stores.pgvector.collection2 import PGVectorCollection
from sqlalchemy.schema import CreateTable, DropTable

from sqlalchemy import MetaData
from sqlalchemy.sql import text
from sqlalchemy.schema import CreateSchema
from sqlalchemy.ext.declarative import declarative_base
from vectorapi.stores.pgvector.db import init_db_engine
from loguru import logger
from vectorapi.stores.pgvector.base import Base

from sqlalchemy import BLOB
from sqlalchemy import event
from sqlalchemy import PickleType
from sqlalchemy import Table
from pgvector.sqlalchemy import Vector
from pgvector.asyncpg import register_vector


# @event.listens_for(Table, "column_reflect")
# def _setup_pickletype(inspector, table, column_info):
#     print(column_info)
#     if isinstance(column_info["type"], "Vector"):
#         column_info["type"] = Vector()


class PGVectorClient(Client):
    def __init__(self):
        self.engine, self.bound_async_sessionmaker = init_db_engine()
        self._metadata = Base.metadata

    async def setup(self):
        async with self.engine.begin() as conn:
            await conn.execute(CreateSchema(SCHEMA_NAME, if_not_exists=True))
        await self.sync()

    async def sync(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(self._metadata.reflect)

    async def create_collection(self, name: str, dimension: int) -> Collection:
        ## TODO: do the init bit during initialisation
        logger.info(f"Creating collection name={name} dimension={dimension}")
        collection = PGVectorCollection(
            name=name, dimension=dimension, session_maker=self.bound_async_sessionmaker
        )
        collection.build_table()
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(self._metadata.create_all)
        except Exception as e:
            logger.exception(e)
            raise e
        return collection

    async def get_collection(self, name: str) -> Optional[Collection]:
        logger.info(f"Getting collection name={name}")
        try:
            table = self._metadata.tables.get(f"{SCHEMA_NAME}.{name}")
            if table is not None:
                return PGVectorCollection(
                    name=name,
                    dimension=table.c.embedding.type.dim,
                    session_maker=self.bound_async_sessionmaker,
                )
            else:
                logger.info(f"Table {name} does not exist")
                return None
        except Exception as e:
            logger.exception(e)
            raise e

    async def delete_collection(self, name: str):
        logger.info(f"Deleting collection name={name}")
        try:
            table = self._metadata.tables.get(f"{SCHEMA_NAME}.{name}")
            if table is not None:
                async with self.engine.begin() as conn:
                    await conn.run_sync(table.drop)
            else:
                logger.info(f"Table {name} does not exist")
                raise Exception(f"Table {name} does not exist")
        except Exception as e:
            logger.exception(e)
            raise e

    async def list_collections(self):
        logger.info("Listing collection..")
        return [
            {"name": table.name, "dimension": table.c.embedding.type.dim}
            for table in self._metadata.tables.values()
        ]

    async def collection_exists(self, name: str) -> bool:
        return name in self._metadata.tables.keys()


# async def get_pgvector_client() -> Client:
#     """get_client returns the client instance."""
#     client = PGVectorClient()
#     await client.init_db()
#     return client
