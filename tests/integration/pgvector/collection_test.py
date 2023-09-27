import os

import pytest
import pytest_asyncio
from sqlalchemy import text

from vectorapi.models.collection import CollectionPoint, CollectionPointResult
from vectorapi.stores.exceptions import CollectionPointNotFound
from vectorapi.stores.pgvector.client import PGVectorClient

TEST_SCHEMA_NAME = os.getenv("VECTORAPI_STORE_SCHEMA")
test_collection_name = "test_collection_point"

pytestmark = pytest.mark.asyncio


class TestPGVectorCollection:
    @pytest_asyncio.fixture()
    async def client(self):
        pg_client = PGVectorClient()
        await pg_client.setup()
        return pg_client

    @pytest.mark.integration
    async def test_insert_point(self, client):
        ## Create collection
        collection = await client.create_collection(test_collection_name, 2)

        ## Add point into collection
        await collection.insert("1", [1.0, 2.0], {})

        points = await self._read_point(client, "1")
        assert len(points) == 1

        ## Cleanup
        await self._cleanup_collection(client)

    @pytest.mark.integration
    async def test_get_point(self, client):
        ## Create collection
        collection = await client.create_collection(test_collection_name, 2)

        ## Get point from empty collection
        with pytest.raises(
            CollectionPointNotFound,
            match=f"Collection point with id 1 not found in collection {test_collection_name}",
        ):
            await collection.get("1")

        ## Add point into collection
        await self._insert_point(client, "1")
        point = await collection.get("1")
        assert isinstance(point, CollectionPoint)
        assert point.id == "1"
        assert point.embedding == [1.0, 2.0]
        assert point.metadata == {}

        ## Cleanup
        await self._cleanup_collection(client)

    @pytest.mark.integration
    async def test_update_point(self, client):
        ## Create collection
        collection = await client.create_collection(test_collection_name, 2)

        ## Insert point to be updated
        await self._insert_point(client, "1")

        ## Update point
        await collection.update("1", [2.0, 3.0], {"metadata_test": "test"})
        point = await self._read_point(client, "1")
        assert len(point) == 1
        assert point[0][0] == "1"
        assert point[0][1] == "[2,3]"
        assert point[0][2] == {"metadata_test": "test"}

        ## Cleanup
        await self._cleanup_collection(client)

    @pytest.mark.integration
    async def test_delete_point(self, client):
        ## Create collection
        collection = await client.create_collection(test_collection_name, 2)

        ## Insert point to be deleted
        await self._insert_point(client, "1")

        ## Delete point
        await collection.delete("1")
        points = await self._read_point(client, "1")
        assert len(points) == 0

        ## Cleanup
        await self._cleanup_collection(client)

    @pytest.mark.integration
    async def test_query_point(self, client):
        # Create collection
        collection = await client.create_collection(test_collection_name, 2)

        # Insert points
        await self._insert_point(client, "1", [1.0, 2.0])
        await self._insert_point(client, "2", [2.0, 3.0])
        await self._insert_point(client, "3", [3.0, 4.0])

        # Query points
        results = await collection.query([1.0, 2.0], limit=2)
        assert len(results) == 2

        assert isinstance(results[0], CollectionPointResult)
        payload_1 = results[0].payload
        assert isinstance(payload_1, CollectionPoint)
        assert payload_1.id == "1"
        assert payload_1.embedding == [1.0, 2.0]
        assert payload_1.metadata == {}
        assert results[0].score == 1.0

        assert isinstance(results[1], CollectionPointResult)
        payload_2 = results[1].payload
        assert isinstance(payload_2, CollectionPoint)
        assert payload_2.id == "2"
        assert payload_2.embedding == [2.0, 3.0]
        assert payload_2.metadata == {}
        assert round(results[1].score, 6) == 0.992278

        # Cleanup
        await self._cleanup_collection(client)

    @pytest.mark.integration
    async def test_upsert_point(self, client):
        # Create collection
        collection = await client.create_collection(test_collection_name, 2)

        # Insert point
        await collection.upsert("1", [1.0, 2.0], {})
        points = await self._read_point(client, "1")
        assert len(points) == 1
        assert points[0][1] == "[1,2]"

        # Upsert point
        await collection.upsert("1", [2.0, 3.0], {"metadata_test": "test"})
        points = await self._read_point(client, "1")
        assert len(points) == 1
        assert points[0][1] == "[2,3]"
        assert points[0][2] == {"metadata_test": "test"}

        # Cleanup
        await self._cleanup_collection(client)

    async def _read_point(self, client, id):
        stmt = f"SELECT id, embedding, metadata FROM {TEST_SCHEMA_NAME}.{test_collection_name} WHERE id = '{id}'"
        async with client.engine.begin() as conn:
            result = await conn.execute(text(stmt))
            return [row for row in result.all()]

    async def _insert_point(self, client, id="1", embedding=[1.0, 2.0], metadata={}):
        stmt = f"INSERT INTO {TEST_SCHEMA_NAME}.{test_collection_name} (id, embedding, metadata) VALUES ('{id}', ARRAY{embedding}, '{metadata}')"
        async with client.engine.begin() as conn:
            await conn.execute(text(stmt))

    async def _cleanup_collection(self, client, collection_name=test_collection_name):
        # TODO: Improve Cleanup
        drop_stmt = f"DROP TABLE IF EXISTS {TEST_SCHEMA_NAME}.{collection_name}"
        async with client.engine.begin() as conn:
            await conn.execute(text(drop_stmt))
