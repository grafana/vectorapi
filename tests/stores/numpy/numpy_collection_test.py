import pytest

from vectorapi.stores.numpy.client import NumpyClient
from vectorapi.models.collection import CollectionPoint

pytestmark = pytest.mark.asyncio


class TestNumpyCollection:
    async def test_insert(self):
        client = NumpyClient()
        collection = await client.create_collection("test_collection", 2)
        await collection.insert("1", [1.0, 2.0], {})
        point = await collection.get("1")
        assert isinstance(point, CollectionPoint)
        assert point.id == "1"
        assert point.embedding == [1.0, 2.0]
        assert point.metadata == {}

    async def test_update(self):
        client = NumpyClient()
        collection = await client.create_collection("test_collection", 2)
        await collection.insert("1", [1.0, 2.0], {})
        await collection.update("1", [2.0, 3.0], {})
        point = await collection.get("1")
        assert point.id == "1"
        assert point.embedding == [2.0, 3.0]
        assert point.metadata == {}

    async def test_delete(self):
        client = NumpyClient()
        collection = await client.create_collection("test_collection", 2)
        await collection.insert("1", [1.0, 2.0], {})
        await collection.delete("1")
        # TODO: Add exceptions
        with pytest.raises(ValueError):
            assert await collection.get("1")

    async def test_query(self):
        client = NumpyClient()
        collection = await client.create_collection("test_collection", 2)
        await collection.insert("1", [1.0, 2.0], {})
        await collection.insert("2", [2.0, 4.0], {})
        await collection.insert("3", [3.0, 5.0], {})
        
        #TODO: cosine similarity seems weird here. We need to spend some time to understand this.
        results = await collection.query([2.0, 4.0], limit=3)
        assert len(results) == 3

    async def test_upsert(self):
        client = NumpyClient()
        collection = await client.create_collection("test_collection", 2)
        await collection.upsert("1", [1.0, 2.0], {})
        await collection.upsert("1", [2.0, 3.0], {})
        point = await collection.get("1")
        assert point.id == "1"
        assert point.embedding == [2.0, 3.0]
        assert point.metadata == {}
