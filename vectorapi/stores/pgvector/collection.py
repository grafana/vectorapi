from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from asyncpg import Connection
from pgvector.sqlalchemy import Vector
from vectorapi.models.client import Client
from vectorapi.models.collection import Collection
from vectorapi.models.collection import CollectionPoint, CollectionPointResult

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
    def __init__(self, name: str, dimension: int, table: Table):
        self.name = name
        self.dimension = dimension
        self.table: Table = table

    async def insert(self, id: str, embedding: List[float], metadata: Dict[str, Any] = {}) -> None:
        # Implement pgvector-specific logic to insert a point into the collection
        # You may need to use SQL queries to insert the data
        pass

    async def update(self, id: str, embedding: List[float], metadata: Dict[str, Any] = {}) -> None:
        # Implement pgvector-specific logic to update a point in the collection
        # You may need to use SQL queries to update the data
        pass

    async def upsert(self, id: str, embedding: List[float], metadata: Dict[str, Any] = {}) -> None:
        # Implement pgvector-specific logic to upsert (insert or update) a point in the collection
        # You may need to use SQL queries to upsert the data
        pass

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

    @classmethod
    async def create(cls, name, dimension, engine) -> "PGVectorCollection":
        # Implement logic to create a PGVectorCollection instance
        # This may involve setting up the collection in pgvector or performing any other necessary tasks
        # Return the created PGVectorCollection instance
        # Define the SQL statement to create a table for vector data
        table = Table(
            name,
            Column("id", String, primary_key=True),
            Column("vec", Vector(dimension), nullable=False),
            Column(
                "metadata",
                postgresql.JSONB,
                server_default=text("'{}'::jsonb"),
                nullable=True,
            ),
        )
        with engine.begin() as conn:
            conn.run_sync(table.create)
        return cls(name, dimension, table)

    def __repr__(self):
        return f"PGVectorCollection(name={self.name}, dimension={self.dimension})"


# # def build_table(name: str, meta: MetaData, dimension: int) -> Table:
# #     """
# #     PRIVATE

# #     Builds a SQLAlchemy model

# #     Args:
# #         name (str): The name of the table.
# #         dimension: The dimension of the vectors in the collection.
# #         metadatas: Dict[str, Dict[str, Any]] = {}

# #     Returns:
# #         Table: The constructed SQL table.
# #     """
# #     return Table(
# #         name,
# #         Column("id", String, primary_key=True),
# #         Column("vec", Vector(dimension), nullable=False),
# #         Column(
# #             "metadata",
# #             postgresql.JSONB,
# #             server_default=text("'{}'::jsonb"),
# #             nullable=True,
# #         ),
# #         extend_existing=True,
# #     )
