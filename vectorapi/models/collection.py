from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Extra


class CollectionPoint(BaseModel):
    id: str
    embedding: List[float] = []
    metadata: Dict[str, Any] = {}


class CollectionPointResult(BaseModel):
    payload: CollectionPoint
    score: float


class Collection(BaseModel, ABC, extra=Extra.allow):
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
        self, embedding: List[float], limit: int, filter: Optional[Dict[str, Any]] = None
    ) -> List[CollectionPointResult]:
        raise NotImplementedError()

    def __repr__(self):
        return f"Collection(name={self.name}, dimension={self.dimension})"
