from abc import ABC, abstractmethod
from typing import List, Optional

from vectorapi.models.collection import Collection


class Client(ABC):
    def __init__(self):
        pass

    @abstractmethod
    async def create_collection(self, name: str, dimension: int) -> Collection:
        raise NotImplementedError()

    @abstractmethod
    async def get_collection(self, name: str) -> Optional[Collection]:
        raise NotImplementedError()

    async def get_or_create_collection(self, name: str, dimension: int) -> Collection:
        collection = await self.get_collection(name)
        if collection is None:
            return await self.create_collection(name, dimension)
        return collection

    @abstractmethod
    async def delete_collection(self, name: str):
        raise NotImplementedError()

    @abstractmethod
    async def list_collections(self) -> List[Collection]:
        raise NotImplementedError()

    async def setup(self):
        pass

    async def teardown(self):
        pass
