from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CollectionPoint(BaseModel):
    id: str
    embedding: List[float]
    metadata: Dict[str, Any] = {}


class CollectionPointResult(BaseModel):
    payload: CollectionPoint
    score: float


class Collection(BaseModel, ABC):
    name: str
    dimension: int

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
    ) -> List[CollectionPointResult]:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    async def create(cls, name: str, dimension: int):
        return cls(name, dimension)

    def __repr__(self):
        return f"Collection(name={self.name}, dimension={self.dimension})"
