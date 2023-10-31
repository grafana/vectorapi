import os

import pytest
import pytest_asyncio
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, Table, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from sqlalchemy.schema import CreateTable, DropSchema

import vectorapi.exceptions as exception
from vectorapi.pgvector.client import PGVectorClient
from vectorapi.pgvector.client_settings import Settings
from vectorapi.pgvector.collection import PGVectorCollection
from vectorapi.pgvector.db import init_db_engine

TEST_SCHEMA_NAME = os.getenv("VECTORAPI_STORE_SCHEMA")
test_collection_name = "test_collection"

pytestmark = pytest.mark.asyncio


class TestPGVectorClientIntegration:
    @pytest_asyncio.fixture()
    async def engine(self) -> AsyncEngine:
        settings = Settings()
        return init_db_engine(settings)

    @pytest_asyncio.fixture()
    async def client(self, engine: AsyncEngine) -> PGVectorClient:
        bound_async_sessionmaker = async_sessionmaker(
            bind=engine,
            autoflush=False,
            future=True,
        )
        pg_client = PGVectorClient(engine, bound_async_sessionmaker)
        return pg_client

    @pytest.mark.integration
    async def test_create_collection(self, client: PGVectorClient):
        await client.create_collection(test_collection_name, 3)

        assert self._get_collection(client) is not None
        await self._cleanup_db(client)

    @pytest.mark.integration
    async def test_get_collection(self, client: PGVectorClient):
        with pytest.raises(
            exception.CollectionNotFound,
            match="Table test_collection does not exist in schema test_schema",
        ):
            await client.get_collection(test_collection_name)
        await self._create_test_collection(client)
        collection = await client.get_collection(test_collection_name)
        assert isinstance(collection, PGVectorCollection)
        await self._cleanup_db(client)

    @pytest.mark.integration
    async def test_delete_collection(self, client: PGVectorClient):
        # Delete non-existent collection
        with pytest.raises(
            exception.CollectionNotFound,
            match="Table test_collection does not exist in schema test_schema",
        ):
            await client.delete_collection(test_collection_name)

        await self._create_test_collection(client)
        await client.delete_collection(test_collection_name)

        assert self._get_collection(client) is None
        await self._cleanup_db(client)

    @pytest.mark.integration
    async def test_list_collections(self, client: PGVectorClient):
        collections = await client.list_collections()
        assert collections == []
        await self._create_test_collection(client)
        collections = await client.list_collections()
        assert collections == [{"name": test_collection_name, "dimension": 2}]
        await self._cleanup_db(client)

    @pytest.mark.integration
    async def test_get_or_create_collection(self, client: PGVectorClient):
        collection = await client.get_or_create_collection(test_collection_name, 2)
        assert isinstance(collection, PGVectorCollection)

        assert self._get_collection(client) is not None

        await self._cleanup_db(client)

    async def _cleanup_db(self, client: PGVectorClient, collection_name=test_collection_name):
        # TODO: Improve Cleanup
        async with client.engine.begin() as conn:
            if client._metadata.tables:
                client._metadata.remove(
                    client._metadata.tables.get(f"{TEST_SCHEMA_NAME}.{collection_name}")
                )
            await conn.execute(DropSchema(TEST_SCHEMA_NAME, cascade=True))

    async def _create_test_collection(self, client: PGVectorClient):
        collection = Table(
            test_collection_name,
            client._metadata,
            Column("id", String, primary_key=True),
            Column("embedding", Vector(2), nullable=False),
            Column(
                "metadatas",
                postgresql.JSONB,
                server_default=text("'{}'::jsonb"),
                nullable=False,
            ),
            extend_existing=True,
        )
        create_expression = CreateTable(collection)
        async with client.engine.begin() as conn:
            await conn.execute(create_expression)
            await client.sync()

    def _get_collection(self, client: PGVectorClient, collection_name=test_collection_name):
        return client._metadata.tables.get(f"{TEST_SCHEMA_NAME}.{collection_name}")
