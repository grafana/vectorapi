from typing import Annotated, Any, Dict, List, Optional

import numpy as np
import orjson
from numpy.typing import NDArray
from pydantic import BeforeValidator, PlainSerializer

from vectorapi.models.collection import Collection, CollectionPoint


def nd_array_custom_before_validator(x):
    # custome before validation logic
    return x


def nd_array_custom_serializer(x):
    # custome serialization logic
    return orjson.dumps(x, option=orjson.OPT_SERIALIZE_NUMPY).decode()


NdArray = Annotated[
    NDArray[np.float_],
    BeforeValidator(nd_array_custom_before_validator),
    PlainSerializer(nd_array_custom_serializer, return_type=str),
]


class NumpyCollection(Collection):
    vectors: NdArray = np.empty(0)
    metadatas: Dict[str, Dict[str, Any]] = {}

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, name: str, dimension: int) -> None:
        super().__init__(name=name, dimension=dimension)
        self.vectors = np.empty((0, dimension))

    @property
    def ids(self) -> List[str]:
        return list(self.metadatas.keys())

    async def insert(self, id: str, embedding: List[float], metadata: Dict[str, Any]) -> None:
        if id in self.ids:
            raise ValueError(f"Vector with id {id} already exists")
        self.metadatas[id] = metadata
        self.vectors = np.vstack([self.vectors, embedding])

    async def update(self, id: str, embedding: List[float], metadata: Dict[str, Any]) -> None:
        if id not in self.ids:
            raise ValueError(f"Vector with id {id} does not exist")
        idx = self.ids.index(id)
        self.vectors[idx] = embedding
        self.metadatas[id] = metadata

    async def upsert(self, id: str, embedding: List[float], metadata: Dict[str, Any]) -> None:
        if id not in self.ids:
            await self.insert(id, embedding, metadata)
        else:
            idx = self.ids.index(id)
            self.vectors[idx] = embedding
            self.metadatas[id] = metadata

    async def delete(self, id: str) -> None:
        if id not in self.ids:
            raise ValueError(f"Vector with id {id} does not exist")
        idx = self.ids.index(id)
        np.delete(self.vectors, idx, 0)
        del self.metadatas[id]

    async def get(self, id: str) -> CollectionPoint:
        if id not in self.ids:
            raise ValueError(f"Vector with id {id} does not exist")
        idx = self.ids.index(id)
        return CollectionPoint(id=id, embedding=self.vectors[idx], metadata=self.metadatas[id])

    async def query(
        self, embedding: List[float], limit: int, filters: Optional[Dict[str, Any]] = None
    ) -> List[CollectionPoint]:
        # search nearest embeddings with cosine similarity, return top N
        similarities = self._cosine_similarity(np.array(embedding), self.vectors)
        top_k_idx = np.argsort(similarities)[::-1][:limit]
        return sorted(
            [
                CollectionPoint(
                    id=self.ids[i], embedding=self.vectors[i], metadata=self.metadatas[i]
                )
                for i in top_k_idx
            ],
            key=lambda x: x.similarity,
            reverse=True,
        )

    def _cosine_similarity(
        self, a: NDArray[np.float_], b: NDArray[np.float_], normalize: bool = True
    ) -> NDArray[np.float_]:
        similarity = np.matmul(a, b.T)
        if normalize:
            similarity /= np.linalg.norm(a) * np.linalg.norm(b, axis=1)
        return similarity

    @classmethod
    async def create(cls, name: str, dimension: int):
        return cls(name, dimension)

    def __repr__(self):
        return f"NumpyCollection(name={self.name}, dimension={self.dimension})"

    # def __init__(self, name: str, dimension: int) -> None:
    #     super().__init__(name, dimension)
    #     self.vectors = np.zeros((0, dimension))
    #     self.metadata = {}

    # async def upsert(
    #     self, id: str, embedding: NDArray[np.float_], metadata: Dict[str, Any]
    # ) -> None:
    #     self.vectors = np.vstack([self.vectors, embedding])
    #     self.metadata[id] = metadata

    # async def delete(self, id: str) -> None:
    #     self.vectors = np.delete(self.vectors, id, 0)
    #     del self.metadata[id]

    # async def fetch(self, id: str) -> CollectionPoint:
    #     return CollectionPoint(id=id, embedding=self.vectors[id], metadata=self.metadata[id])

    # async def query(
    #     self, embedding: NDArray[np.float_], limit: int, filter: Optional[Dict[str, Any]] = None
    # ) -> List:
    #     # search nearest embeddings with cosine similarity, return top N
    #     similarities = self._cosine_similarity(embedding, self.vectors)
    #     top_k_idx = np.argsort(similarities)[::-1][:limit]
    #     return sorted(
    #         [CollectionPoint(embedding=self.vectors[i], metadata=self.metadata[i]) for i in top_k_idx],
    #         key=lambda x: x.similarity,
    #         reverse=True,
    #     )

    # def _filter_by_metadata(self, filter: Dict[str, Any]):
    #     pass

    # def _cosine_similarity(
    #     self, a: NDArray[np.float_], b: NDArray[np.float_], normalize: bool = True
    # ):
    #     similarity = np.matmul(a, b.T)
    #     if normalize:
    #         similarity /= np.linalg.norm(a) * np.linalg.norm(b, axis=1)
    #     return similarity
