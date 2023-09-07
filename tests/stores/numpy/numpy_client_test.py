import pytest
from vectorapi.models.collection import Collection
from vectorapi.stores.numpy.client import NumpyClient


@pytest.mark.asyncio
class TestNumpyClient:

    async def test_create_collection(self):
        client = NumpyClient()
        collection = await client.create_collection("test_collection", 2)
        assert isinstance(collection, Collection)
        assert collection.name == "test_collection"

    async def test_get_collection(self):
        client = NumpyClient()
        await client.create_collection("test_collection", 2)
        collection = await client.get_collection("test_collection")
        assert isinstance(collection, Collection)
        assert collection.name == "test_collection"

    async def test_delete_collection(self):
        client = NumpyClient()
        await client.create_collection("test_collection", 2)
        await client.delete_collection("test_collection")
        assert await client.get_collection("test_collection") is None

    async def test_list_collections(self):
        client = NumpyClient()
        await client.create_collection("test_collection", 2)
        await client.create_collection("test_collection2", 200)
        collections = await client.list_collections()
        assert len(collections) == 2
        assert collections[0].name == "test_collection"
        assert collections[0].dimension == 2

        assert collections[1].name == "test_collection2"
        assert collections[1].dimension == 200