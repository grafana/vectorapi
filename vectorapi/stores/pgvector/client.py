from typing import Optional

from loguru import logger

from vectorapi.models.client import Client
from vectorapi.models.collection import Collection
from vectorapi.stores.pgvector.base import Base
from vectorapi.stores.pgvector.collection import PGVectorCollection
from vectorapi.stores.pgvector.const import VECTORAPI_STORE_SCHEMA
from vectorapi.stores.pgvector.db import init_db_engine
from vectorapi.stores.exceptions import CollectionNotFound


class PGVectorClient(Client):
    def __init__(self):
        self.engine, self.bound_async_sessionmaker = init_db_engine()
        self._metadata = Base.metadata

    async def setup(self):
        await self.sync()

    async def sync(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(self._metadata.reflect)

    async def create_collection(self, name: str, dimension: int) -> Collection:
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
            if self._collection_exists(name):
                table = self._metadata.tables.get(f"{VECTORAPI_STORE_SCHEMA}.{name}")
                return PGVectorCollection(
                    name=name,
                    dimension=table.c.embedding.type.dim,
                    session_maker=self.bound_async_sessionmaker,
                )
            else:
                raise CollectionNotFound(f"Table {name} does not exist in schema {VECTORAPI_STORE_SCHEMA}")
        except Exception as e:
            logger.exception(e)
            raise e

    async def delete_collection(self, name: str):
        logger.info(f"Deleting collection name={name}")
        try:
            if self._collection_exists(name):
                table = self._metadata.tables.get(f"{VECTORAPI_STORE_SCHEMA}.{name}")
                async with self.engine.begin() as conn:
                    await conn.run_sync(table.drop)
                    self._metadata.remove(table)
            else:
                raise CollectionNotFound(f"Table {name} does not exist in schema {VECTORAPI_STORE_SCHEMA}")
        except Exception as e:
            logger.exception(e)
            raise e

    async def list_collections(self):
        logger.info("Listing collection..")
        return [
            {"name": table.name, "dimension": table.c.embedding.type.dim}
            for table in self._metadata.tables.values()
        ]

    def _collection_exists(self, name: str) -> bool:
        return f"{VECTORAPI_STORE_SCHEMA}.{name}" in self._metadata.tables.keys()
