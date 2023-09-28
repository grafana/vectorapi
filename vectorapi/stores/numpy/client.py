from typing import Dict, List

from vectorapi.models.client import Client
from vectorapi.stores.exceptions import CollectionNotFound
from vectorapi.stores.numpy.collection import NumpyCollection


class NumpyClient(Client):
    def __init__(self):
        self.collections: Dict[str, NumpyCollection] = {}

    async def create_collection(self, name: str, dimension: int) -> NumpyCollection:
        if name in self.collections:
            raise ValueError(f"Collection with name {name} already exists")
        self.collections[name] = NumpyCollection(name, dimension)
        return self.collections[name]

    async def get_collection(self, name: str) -> NumpyCollection:
        collection = self.collections.get(name)
        if collection is None:
            raise CollectionNotFound(f"Collection with name {name} does not exist")
        return collection

    async def delete_collection(self, name: str):
        if await self.get_collection(name):
            del self.collections[name]
        else:
            raise ValueError(f"Collection with name {name} does not exist")

    async def list_collections(self) -> List[NumpyCollection]:  # type: ignore
        return list(self.collections.values())
