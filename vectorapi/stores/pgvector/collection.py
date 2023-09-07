from typing import Any, Dict, List, Optional

from pgvector.sqlalchemy import Vector
from vectorapi.models.collection import Collection
from vectorapi.models.collection import CollectionPoint, CollectionPointResult
from sqlalchemy.schema import CreateTable
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
import os

from sqlalchemy.dialects import postgresql
from sqlalchemy import (
    Column,
    String,
    Table,
    Integer,
    Float,
    text,
    bindparam,
    ARRAY
)

##TODO: Pass this from the client
SCHEMA_NAME = os.getenv("POSTGRES_SCHEMA_NAME")

# class PGVectorCollection(Collection):
class PGVectorCollection(Collection):
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
        # statement = postgresql.insert(self._embeddings).values((id, embedding, metadata))
        # stmt = text(f"INSERT INTO vector.{self.name} (id, embedding, metadata) VALUES ('3', '[3,1,2]')")

        ##TODO: Text injection here is a security risk
        # stmt = text(f"INSERT INTO {SCHEMA_NAME}.{self.name} (id, embeddings, metadata) VALUES (:id, ARRAY:embedding, :metadata);")
        stmt = text(f"INSERT INTO {SCHEMA_NAME}.{self.name} (id, embeddings, metadata) VALUES (:id, :embedding, :metadata);")

        stmt = stmt.bindparams(
            bindparam("id", type_= String),
            # bindparam("embedding", type_= postgresql.ARRAY(Float, dimensions=self.dimension)),
            bindparam("embedding", type_= Vector),
            bindparam("metadata", type_= postgresql.JSONB)
        )
        async with self._session_maker() as session:
            await session.execute(statement=stmt, params={"id": id, "embedding": embedding, "metadata": metadata})
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
        # statement = postgresql.query(self._embeddings).values((str(embedding)))

        ##TODO: Text injection here is a security risk
        # stmt = text(f"SELECT * FROM {SCHEMA_NAME}.{self.name} ORDER BY embeddings <-> :embedding LIMIT :limit;")
        stmt = text(f"SELECT *, 1 - (embeddings <=> :embedding) AS cosine_similarity FROM {SCHEMA_NAME}.{self.name} ORDER BY embeddings <=> :embedding LIMIT :limit;")
        stmt = stmt.bindparams(
            bindparam("embedding", type_= Vector),
            bindparam("limit", type_= Integer)
        )
        async with self._session_maker() as session:
            result = await session.execute(stmt, {"embedding": embedding, "limit": limit})
        res = [
            ## Do we return the embedding here or just the metadata?
            CollectionPointResult(
                id=row[0],
                metadata=row[2],
                score=row[3],
            )
            for row in result.all()
        ]
        return res

    async def create(self, session_maker, metadata) -> "PGVectorCollection":
        # Implement logic to create a PGVectorCollection instance
        # This may involve setting up the collection in pgvector or performing any other necessary tasks
        # Return the created PGVectorCollection instance
        embeddings = Table(
                    self.name,
                    metadata,
                Column("id", String, primary_key=True),
                # Column("embeddings", postgresql.ARRAY(Float, dimensions=self.dimension), nullable=False),
                Column("embeddings", Vector(self.dimension), nullable=False),
                Column(
                    "metadata",
                    postgresql.JSONB,
                    server_default=text("'{}'::jsonb"),
                    nullable=False,
                ),
                extend_existing=True,
                )
        create_expression = CreateTable(embeddings, if_not_exists=True)
        async with session_maker() as session:
            await session.execute(create_expression)
            await session.commit()
        return

    # async def create(self, session_maker, metadata) -> "PGVectorCollection":
    #     stmt = text(f"CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.{self.name} (id text PRIMARY KEY, embeddings vector({self.dimension}), metadata jsonb);")
    #     async with session_maker() as session:
    #         await session.execute(stmt)
    #         await session.commit()

    def __repr__(self):
        return f"PGVectorCollection(name={self.name}, dimension={self.dimension})"
