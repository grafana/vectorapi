from vectorapi.models.collection import Collection
from typing import Dict, Any, Optional, List
import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel


class NumpyPoint(BaseModel):
    embedding: NDArray[np.float_]
    metadata: Dict[str, Any]


class NumpyCollection(Collection):
    def __init__(self, name: str, dimension: int) -> None:
        super().__init__(name, dimension)
        self.vectors = np.zeros((0, dimension))
        self.metadata = {}

    async def upsert(
        self, id: str, embedding: NDArray[np.float_], metadata: Dict[str, Any]
    ) -> None:
        self.vectors = np.vstack([self.vectors, embedding])
        self.metadata[id] = metadata

    async def delete(self, id: str) -> None:
        self.vectors = np.delete(self.vectors, id, 0)
        del self.metadata[id]

    async def fetch(self, id: str) -> NumpyPoint:
        return NumpyPoint(embedding=self.vectors[id], metadata=self.metadata[id])

    async def query(
        self, embedding: NDArray[np.float_], limit: int, filter: Optional[Dict[str, Any]] = None
    ) -> List:
        # search nearest embeddings with cosine similarity, return top N
        similarities = self._cosine_similarity(embedding, self.vectors)
        top_k_idx = np.argsort(similarities)[::-1][:limit]
        return sorted(
            [NumpyPoint(embedding=self.vectors[i], metadata=self.metadata[i]) for i in top_k_idx],
            key=lambda x: x.similarity,
            reverse=True,
        )

    def _filter_by_metadata(self, filter: Dict[str, Any]):
        pass

    def _cosine_similarity(
        self, a: NDArray[np.float_], b: NDArray[np.float_], normalize: bool = True
    ):
        similarity = np.matmul(a, b.T)
        if normalize:
            similarity /= np.linalg.norm(a) * np.linalg.norm(b, axis=1)
        return similarity
