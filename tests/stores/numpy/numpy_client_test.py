import pytest

from vectorapi.stores.numpy.client import NumpyClient

pytestmark = pytest.mark.asyncio


class TestNumpyClient:
    async def test_create_collection(self):
        client = NumpyClient()
        collection = await client.create_collection("test_collection", 2)
        assert collection.name == "test_collection"
        assert collection.dimension == 2

    async def test_get_collection(self):
        client = NumpyClient()
        assert await client.get_collection("test_collection") is None

        collection = await client.create_collection("test_collection", 2)
        assert await client.get_collection("test_collection") == collection

    async def test_delete_collection(self):
        client = NumpyClient()
        await client.create_collection("test_collection", 2)
        await client.delete_collection("test_collection")
        assert await client.get_collection("test_collection") is None

    async def test_list_collections(self):
        client = NumpyClient()
        await client.create_collection("test_collection", 2)
        collections = await client.list_collections()
        assert len(collections) == 1
        assert collections[0].name == "test_collection"
        assert collections[0].dimension == 2
