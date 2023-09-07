from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from asyncpg import Connection
from pgvector.sqlalchemy import Vector
from vectorapi.models.client import Client
from vectorapi.models.collection import Collection
from vectorapi.models.collection import CollectionPoint, CollectionPointResult
from sqlalchemy.schema import CreateTable, DropTable
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.dialects import postgresql
from sqlalchemy import (
    Column,
    MetaData,
    String,
    Table,
    text,
)

# class PGVectorCollection(Collection):
class PGVectorCollection(Collection):
    _embeddings: Table
    _session_maker: AsyncSession


    class Config:
        arbitrary_types_allowed = True

    # def __init__(self, name: str, dimension: int, collection: Table) -> None:
    def __init__(self, name: str, dimension: int) -> None:
        super().__init__(name=name, dimension=dimension)

    async def insert(self, id: str, embedding: List[float], metadata: Dict[str, Any] = {}) -> None:
        # Implement pgvector-specific logic to insert a point into the collection
        # You may need to use SQL queries to insert the data
        pass

    async def update(self, id: str, embedding: List[float], metadata: Dict[str, Any] = {}) -> None:
        # Implement pgvector-specific logic to update a point in the collection
        # You may need to use SQL queries to update the data
        pass

    async def upsert(self, id: str, embedding: List[float], metadata: Dict[str, str]) -> None:
        # Implement pgvector-specific logic to insert a point into the collection
        # You may need to use SQL queries to insert the data
        statement = postgresql.insert(self._embeddings).values((id, embedding, metadata))
        async with self._session_maker() as session:
            await session.execute(statement=statement)
            await session.commit()

    async def delete(self, id: str) -> None:
        # Implement pgvector-specific logic to delete a point from the collection
        # You may need to use SQL queries to delete the data
        pass

    async def get(self, id: str) -> CollectionPoint:
        # Implement pgvector-specific logic to retrieve a point by ID from the collection
        # You may need to use SQL queries to fetch the data
        # Return a CollectionPoint object with the retrieved data
        pass

    async def query(
        self, embedding: List[float], limit: int, filters: Optional[Dict[str, Any]] = None
    ) -> List[CollectionPointResult]:
        # Implement pgvector-specific logic to query the collection based on the provided embedding
        # You may need to use SQL queries to perform the search
        # Return a list of CollectionPointResult objects with the query results
        pass

    async def create(self, session_maker, metadata) -> "PGVectorCollection":
        # Implement logic to create a PGVectorCollection instance
        # This may involve setting up the collection in pgvector or performing any other necessary tasks
        # Return the created PGVectorCollection instance
        embeddings = Table(
                    self.name,
                    metadata,
                Column("id", String, primary_key=True),
                Column("embeddings", Vector(self.dimension), nullable=False),
                Column(
                    "metadata",
                    postgresql.JSONB,
                    server_default=text("'{}'::jsonb"),
                    nullable=False,
                ),
                extend_existing=True,
                )
        create_expression = CreateTable(embeddings)
        async with session_maker() as session:
            await session.execute(create_expression)
            await session.commit()
        self._embeddings = embeddings
        self._session_maker = session_maker
        return self

    def __repr__(self):
        return f"PGVectorCollection(name={self.name}, dimension={self.dimension})"
