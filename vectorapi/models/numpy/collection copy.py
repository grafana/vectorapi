from typing import List, Dict, Any, Optional
from abc import ABCMeta, abstractmethod


class Collection(ABCMeta):
    def __init__(self, name: str, dimension: int) -> None:
        self.name = name
        self.dimension = dimension

    @abstractmethod
    async def upsert(self, id: str, embedding: List[float], metadata: Dict[str, Any]) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def delete(self, id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def fetch(self, id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def query(
        self, embedding: List[float], limit: int, filters: Optional[Dict[str, Any]] = None
    ):
        raise NotImplementedError()

    @abstractmethod
    async def create(self):
        pass

    def __repr__(self):
        return f"Collection(name={self.name}, dimension={self.dimension})"
