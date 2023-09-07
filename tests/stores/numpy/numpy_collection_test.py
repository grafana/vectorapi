import pytest
from vectorapi.models.collection import Collection
from vectorapi.stores.numpy.collection import NumpyCollection


@pytest.mark.asyncio
class TestNumpyCollection:
    def test_create_collection(self):
        collection = NumpyCollection("test_collection", 2)
        assert isinstance(collection, Collection)
        assert collection.name == "test_collection"

    async def test_upsert(self):
        collection = NumpyCollection("test_collection", 2)
        await collection.upsert("test_id", [1, 2], {"url": "custom_url"})
        
        col = await collection.get("test_id")
        assert col.id == "test_id"

    
    async def test_delete(self):
        collection = NumpyCollection("test_collection", 2)
        await collection.upsert("test_id", [1, 2], {"url": "custom_url"})
        assert await collection.get("test_id") is not None

        await collection.delete("test_id")
        assert ValueError("Vector with id test_id does not exist")
    
    async def test_query(self):
        Collection = NumpyCollection("test_collection", 2)
        await Collection.upsert("test_id", [1, 1], {"url": "custom_url"})
        await Collection.upsert("test_id2", [1, 2], {"url": "custom_url2"})
        await Collection.upsert("test_id3", [1, 3], {"url": "custom_url3"})

        results = await Collection.query([1, 1], limit=2)
        assert results[0].id == "test_id"
        assert results[1].id == "test_id2"
    
        assert len(results) == 2