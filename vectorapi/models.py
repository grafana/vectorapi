from typing import Any, Dict, List

from pydantic import BaseModel


class CollectionPoint(BaseModel):
    id: str
    embedding: List[float] = []
    metadata: Dict[str, Any] = {}


class CollectionPointResult(BaseModel):
    payload: CollectionPoint
    score: float
