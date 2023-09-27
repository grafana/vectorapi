import os

import pytest
import pytest_asyncio
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, Table, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable, DropSchema

import vectorapi.stores.exceptions as exception
from vectorapi.models.client import Client
from vectorapi.stores.pgvector.client import PGVectorClient
from vectorapi.stores.pgvector.collection import PGVectorCollection

TEST_SCHEMA_NAME = os.getenv("VECTORAPI_STORE_SCHEMA")
test_collection_name = "test_collection"

pytestmark = pytest.mark.asyncio


class TestPGVectorClient:
    @pytest_asyncio.fixture()
    async def client(self) -> Client:
        pg_client = PGVectorClient()
        await pg_client.setup()
        return pg_client

    @pytest.mark.integration
    async def test_create_collection(self, client):
        await client.create_collection(test_collection_name, 3)

        assert self._get_collection(client) is not None
        await self._cleanup_db(client)

    @pytest.mark.integration
    async def test_get_collection(self, client):
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
    async def test_delete_collection(self, client):
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
    async def test_list_collections(self, client):
        collections = await client.list_collections()
        assert collections == []
        await self._create_test_collection(client)
        collections = await client.list_collections()
        assert collections == [{"name": test_collection_name, "dimension": 2}]
        await self._cleanup_db(client)

    @pytest.mark.integration
    async def test_get_or_create_collection(self, client):
        collection = await client.get_or_create_collection(test_collection_name, 2)
        assert isinstance(collection, PGVectorCollection)

        assert self._get_collection(client) is not None

        await self._cleanup_db(client)

    async def _cleanup_db(self, client, collection_name=test_collection_name):
        # TODO: Improve Cleanup
        async with client.engine.begin() as conn:
            if client._metadata.tables:
                client._metadata.remove(
                    client._metadata.tables.get(f"{TEST_SCHEMA_NAME}.{collection_name}")
                )
            await conn.execute(DropSchema(TEST_SCHEMA_NAME, cascade=True))

    async def _create_test_collection(self, client):
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

    def _get_collection(self, client, collection_name=test_collection_name):
        return client._metadata.tables.get(f"{TEST_SCHEMA_NAME}.{collection_name}")
