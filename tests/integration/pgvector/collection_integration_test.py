import json
import os

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from vectorapi.exceptions import CollectionPointFilterError, CollectionPointNotFound
from vectorapi.models import CollectionPoint, CollectionPointResult
from vectorapi.pgvector.client import PGVectorClient
from vectorapi.pgvector.client_settings import Settings
from vectorapi.pgvector.db import init_db_engine

TEST_SCHEMA_NAME = os.getenv("VECTORAPI_STORE_SCHEMA")
test_collection_name = "test_collection_point"

pytestmark = pytest.mark.asyncio


class TestPGVectorCollectionIntegration:
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
    async def test_insert_point(self, client: PGVectorClient):
        ## Create collection
        collection = await client.create_collection(test_collection_name, 2)

        ## Add point into collection
        await collection.insert("1", [1.0, 2.0], {})

        points = await self._read_point(client, "1")
        assert len(points) == 1

        ## Cleanup
        await self._cleanup_collection(client)

    @pytest.mark.integration
    async def test_get_point(self, client: PGVectorClient):
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
    async def test_update_point(self, client: PGVectorClient):
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
    async def test_delete_point(self, client: PGVectorClient):
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
    async def test_query_point(self, client: PGVectorClient):
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
    @pytest.mark.parametrize(
        "filter_value, expected_ids, expected_metadata",
        [
            (
                "filter1",
                ["1", "3"],
                [{"metadata_filter": "filter1"}, {"metadata_filter": "filter1"}],
            ),
            (
                "filter2",
                ["2", "4"],
                [{"metadata_filter": "filter2"}, {"metadata_filter": "filter2"}],
            ),
        ],
    )
    async def test_query_point_with_filter(
        self, client: PGVectorClient, filter_value, expected_ids, expected_metadata
    ):
        # Create collection
        collection = await client.create_collection(test_collection_name, 2)

        # Insert points
        await self._insert_point(client, "1", [1.0, 2.0], {"metadata_filter": "filter1"})
        await self._insert_point(client, "2", [1.0, 2.0], {"metadata_filter": "filter2"})

        await self._insert_point(client, "3", [3.0, 4.0], {"metadata_filter": "filter1"})
        await self._insert_point(client, "4", [3.0, 4.0], {"metadata_filter": "filter2"})

        await self._insert_point(client, "5", [5.0, 6.0], {"metadata_filter": "filter1"})
        await self._insert_point(client, "6", [5.0, 6.0], {"metadata_filter": "filter2"})

        # Query points with eq filter
        results = await collection.query(
            [1.0, 2.0], limit=2, filter_dict={"metadata_filter": {"$eq": filter_value}}
        )
        assert len(results) == 2

        for i, result in enumerate(results):
            assert result.payload.id == expected_ids[i]
            assert result.payload.metadata == expected_metadata[i]

        await self._cleanup_collection(client)

    @pytest.mark.integration
    async def test_query_point_single_value_filter_exceptions(self, client: PGVectorClient):
        # Create collection
        collection = await client.create_collection(test_collection_name, 2)

        # Insert points
        await self._insert_point(client, "1", [1.0, 2.0], {"metadata_filter": "filter1"})
        await self._insert_point(client, "2", [1.0, 2.0], {"metadata_filter": "filter2"})

        ## Assert raised exception with unsupported filter
        with pytest.raises(
            CollectionPointFilterError,
        ) as excinfo:
            await collection.query(
                [1.0, 2.0], limit=2, filter_dict={"metadata_filter": {"$ee": "filter1"}}
            )
        assert "Unsupported operator $ee" in str(excinfo.value)

        ## Assert raised exception with target filter value not string
        with pytest.raises(
            CollectionPointFilterError,
            match="Filter value must be a string",
        ):
            await collection.query(
                [1.0, 2.0], limit=2, filter_dict={"metadata_filter": {"$eq": ["filter1"]}}
            )

        # Cleanup
        await self._cleanup_collection(client)

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "filter_dict, expected_count, expected_metadata",
        [
            (
                {
                    "$or": [
                        {"metadata_filter_1": {"$eq": "filter1"}},
                        {"metadata_filter_1": {"$eq": "filter2"}},
                    ]
                },
                2,
                [
                    {"metadata_filter_1": "filter1", "metadata_filter_2": "filter1"},
                    {"metadata_filter_1": "filter2", "metadata_filter_2": "filter2"},
                ],
            ),
            (
                {
                    "$and": [
                        {"metadata_filter_1": {"$eq": "filter1"}},
                        {"metadata_filter_2": {"$eq": "filter1"}},
                    ]
                },
                1,
                [{"metadata_filter_1": "filter1", "metadata_filter_2": "filter1"}],
            ),
        ],
    )
    async def test_query_point_logical_operators_filter(
        self, client: PGVectorClient, filter_dict, expected_count, expected_metadata
    ):
        # Create collection
        collection = await client.create_collection(test_collection_name, 2)

        # Insert points
        await self._insert_point(
            client,
            "1",
            [1.0, 2.0],
            {"metadata_filter_1": "filter1", "metadata_filter_2": "filter1"},
        )
        await self._insert_point(
            client,
            "2",
            [1.0, 2.0],
            {"metadata_filter_1": "filter2", "metadata_filter_2": "filter2"},
        )
        await self._insert_point(
            client,
            "3",
            [1.0, 2.0],
            {"metadata_filter_1": "filter3", "metadata_filter_2": "filter3"},
        )

        results = await collection.query([1.0, 2.0], limit=3, filter_dict=filter_dict)

        assert len(results) == expected_count
        for i, result in enumerate(results):
            assert result.payload.metadata == expected_metadata[i]

        # Cleanup
        await self._cleanup_collection(client)

    @pytest.mark.integration
    async def test_upsert_point(self, client: PGVectorClient):
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

    async def _read_point(self, client: PGVectorClient, id):
        stmt = f"SELECT id, embedding, metadata FROM {TEST_SCHEMA_NAME}.{test_collection_name} WHERE id = '{id}'"  # noqa: E501
        async with client.engine.begin() as conn:
            result = await conn.execute(text(stmt))
            return [row for row in result.all()]

    async def _insert_point(
        self, client: PGVectorClient, id="1", embedding=[1.0, 2.0], metadata={}
    ):
        stmt = f"INSERT INTO {TEST_SCHEMA_NAME}.{test_collection_name} (id, embedding, metadata) VALUES ('{id}', ARRAY{embedding}, '{json.dumps(metadata)}')"  # noqa: E501
        async with client.engine.begin() as conn:
            await conn.execute(text(stmt))

    async def _cleanup_collection(self, client, collection_name=test_collection_name):
        # TODO: Improve Cleanup
        drop_stmt = f"DROP TABLE IF EXISTS {TEST_SCHEMA_NAME}.{collection_name}"
        async with client.engine.begin() as conn:
            await conn.execute(text(drop_stmt))
