from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class CollectionPoint:
    def __init__(self, id: str, embedding: List[float], metadata: Dict[str, Any]) -> None:
        self.id = id
        self.embedding = embedding
        self.metadata = metadata


class Collection(ABC):
    def __init__(self, name: str, dimension: int) -> None:
        self.name = name
        self.dimension = dimension

    @abstractmethod
    async def insert(self, id: str, embedding: List[float], metadata: Dict[str, Any]) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def update(self, id: str, embedding: List[float], metadata: Dict[str, Any]) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def upsert(self, id: str, embedding: List[float], metadata: Dict[str, Any]) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def delete(self, id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def get(self, id: str) -> CollectionPoint:
        raise NotImplementedError()

    @abstractmethod
    async def query(
        self, embedding: List[float], limit: int, filters: Optional[Dict[str, Any]] = None
    ) -> List[CollectionPoint]:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    async def create(cls, name: str, dimension: int):
        return cls(name, dimension)

    def __repr__(self):
        return f"Collection(name={self.name}, dimension={self.dimension})"
