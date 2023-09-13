import os
from vectorapi.models.client import Client
from vectorapi.stores.pgvector.client import PGVectorClient
from vectorapi.stores.pgvector.collection import PGVectorCollection
import vectorapi.stores.pgvector.exceptions as exception

import pytest
import pytest_asyncio
from sqlalchemy.schema import DropSchema, CreateTable
from sqlalchemy import Table, Column, String, text
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql


TEST_SCHEMA_NAME = os.getenv("POSTGRES_SCHEMA_NAME")

class TestPGVectorClient_Integration:
    
    @pytest_asyncio.fixture()
    async def client(self) -> Client:
        pg_client = PGVectorClient()
        await pg_client.setup()
        return pg_client

    @pytest.mark.Integration
    @pytest.mark.asyncio
    async def test_create_collection(self, client):
        await client.create_collection("test_collection", 3)
        assert client._metadata.tables.get(f"{TEST_SCHEMA_NAME}.test_collection") is not None
        collection = await client.get_collection("test_collection")
        assert isinstance(collection, PGVectorCollection)
        assert collection.name == "test_collection"
        assert collection.dimension == 3
        await self._cleanup_db(client)

    @pytest.mark.Integration
    @pytest.mark.asyncio
    async def test_get_collection(self, client):
        with pytest.raises(exception.CollectionNotFound, match="Table test_collection does not exist in schema test_schema"):
            await client.get_collection("test_collection")
        await self._create_test_collection(client)
        collection = await client.get_collection("test_collection")
        assert isinstance(collection, PGVectorCollection)
        await self._cleanup_db(client)

    @pytest.mark.Integration
    @pytest.mark.asyncio
    async def test_delete_collection(self, client):
        # Delete non-existent collection
        with pytest.raises(exception.CollectionNotFound, match="Table test_collection does not exist in schema test_schema"):
            await client.delete_collection("test_collection")

        await self._create_test_collection(client)
        await client.delete_collection("test_collection")

        assert client._metadata.tables.get(f"{TEST_SCHEMA_NAME}.test_collection") is None
        await self._cleanup_db(client)

    @pytest.mark.Integration
    @pytest.mark.asyncio
    async def test_list_collections(self, client):
        collections = await client.list_collections()
        assert collections == []
        await self._create_test_collection(client)
        collections = await client.list_collections()
        assert collections == [{"name": "test_collection", "dimension": 2}]
        await self._cleanup_db(client)

    async def _cleanup_db(self, client, collection_name="test_collection"):
        # TODO: Improve Cleanup
        async with client.engine.begin() as conn:
            if client._metadata.tables:
                client._metadata.remove(client._metadata.tables.get(f"{TEST_SCHEMA_NAME}.{collection_name}"))
            await conn.execute(DropSchema(TEST_SCHEMA_NAME, cascade=True))

    async def _create_test_collection(self, client):
        collection = Table(
            "test_collection",
            client._metadata,
        Column("id", String, primary_key=True),
        Column("embedding", Vector(2), nullable=False),
        Column("metadatas",
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
