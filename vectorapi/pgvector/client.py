from fastapi import Depends
from loguru import logger
from typing import Annotated

from vectorapi.models.client import Client
from vectorapi.models.collection import Collection
from vectorapi.exceptions import CollectionNotFound
from vectorapi.pgvector.base import Base
from vectorapi.pgvector.collection import PGVectorCollection
from vectorapi.pgvector.const import VECTORAPI_STORE_SCHEMA
from vectorapi.pgvector.db import engine, bound_async_sessionmaker


class PGVectorClient(Client):
    def __init__(self, engine, bound_async_sessionmaker):
        self.engine = engine
        self.bound_async_sessionmaker = bound_async_sessionmaker
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

    async def get_collection(self, name: str) -> Collection:
        logger.info(f"Getting collection name={name}")
        try:
            if self._collection_exists(name):
                return self._construct_collection(name)

            await self.sync()
            if self._collection_exists(name):
                return self._construct_collection(name)
            else:
                raise CollectionNotFound(
                    f"Table {name} does not exist in schema {VECTORAPI_STORE_SCHEMA}"
                )
        except Exception as e:
            logger.exception(e)
            raise e

    def _construct_collection(self, name: str) -> Collection:
        table = self._metadata.tables.get(f"{VECTORAPI_STORE_SCHEMA}.{name}")
        return PGVectorCollection(
            name=name,
            dimension=table.c.embedding.type.dim,
            session_maker=self.bound_async_sessionmaker,
        )

    async def delete_collection(self, name: str):
        logger.info(f"Deleting collection name={name}")
        try:
            if self._collection_exists(name):
                table = self._metadata.tables.get(f"{VECTORAPI_STORE_SCHEMA}.{name}")
                async with self.engine.begin() as conn:
                    await conn.run_sync(table.drop)
                    self._metadata.remove(table)
            else:
                raise CollectionNotFound(
                    f"Table {name} does not exist in schema {VECTORAPI_STORE_SCHEMA}"
                )
        except Exception as e:
            logger.exception(e)
            raise e

    async def list_collections(self):
        await self.sync()
        logger.info("Listing collection..")
        return [
            {"name": table.name, "dimension": table.c.embedding.type.dim}
            for table in self._metadata.tables.values()
        ]

    def _collection_exists(self, name: str) -> bool:
        return f"{VECTORAPI_STORE_SCHEMA}.{name}" in self._metadata.tables.keys()


async def get_client() -> Client:
    return PGVectorClient(engine, bound_async_sessionmaker)


StoreClient = Annotated[Client, Depends(get_client)]