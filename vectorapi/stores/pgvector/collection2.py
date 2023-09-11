from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List
from pydantic import ConfigDict, Field
from pgvector.sqlalchemy import Vector
from sqlalchemy import String, select, text, delete
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import DropTable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr
from vectorapi.models.collection import Collection
from vectorapi.models.collection import CollectionPoint, CollectionPointResult
from sqlalchemy.ext.asyncio import async_sessionmaker
from vectorapi.stores.pgvector.base import Base
from typing import Type
from typing import Annotated


class CollectionTable(AbstractConcreteBase, Base):
    __abstract__ = True

    # strict_attrs = True
    id: Mapped[str] = mapped_column(
        "id", String, autoincrement=False, nullable=False, unique=True, primary_key=True
    )

    @declared_attr
    def embedding(cls) -> Mapped[List[float]]:
        return mapped_column("embedding", Vector(), nullable=False)

    metadatas: Mapped[Dict[str, Any]] = mapped_column(
        "metadata",
        postgresql.JSONB,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )

    @classmethod
    async def read_all(
        cls, session: AsyncSession, include_metadata: bool
    ) -> AsyncIterator[CollectionTable]:
        stmt = select(cls)
        stream = await session.stream_scalars(stmt.order_by(cls.id))
        async for row in stream:
            yield row

    @classmethod
    async def read_by_id(cls, session: AsyncSession, point_id: str, include_metadata: bool = False):
        stmt = select(cls).where(cls.id == point_id)
        return await session.scalar(stmt.order_by(cls.id))

    @classmethod
    async def create(
        cls, session: AsyncSession, id: str, embedding: List[float], metadata: Dict[str, Any]
    ):
        collection = cls(
            id=id,
            embedding=embedding,
            metadatas=metadata,
        )
        session.add(collection)
        await session.commit()
        await session.flush()
        # # To fetch metadata
        # new = await cls.read_by_id(session, collection.id, include_metadata=True)
        # if not new:
        #     raise RuntimeError()
        # return new

    @classmethod
    async def update(
        cls, session: AsyncSession, id: str, embedding: List[float], metadata: Dict[str, Any]
    ):
        stmt = select(cls).where(cls.id == id)
        result = await session.execute(stmt)
        collection = result.scalar_one_or_none()

        if collection:
            collection.embedding = embedding
            collection.metadatas = metadata

            await session.commit()


    @classmethod
    async def delete(cls, session: AsyncSession, id: str) -> None:
        stmt = delete(cls).where(cls.id == id)
        await session.execute(stmt)
        await session.commit()


class PGVectorCollection(Collection):
    session_maker: async_sessionmaker[AsyncSession] = Field(..., exclude=True)
    table: Type[CollectionTable] | None = Field(default=None, exclude=True)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, **data):
        super().__init__(**data)
        self.table = self.build_table()

    def build_table(self) -> Type[CollectionTable]:
        class CustomCollectionTable(CollectionTable):
            __tablename__ = self.name
            __dimensions__ = self.dimension
            __mapper_args__ = {"polymorphic_identity": self.name, "concrete": True}
            __table_args__ = {"extend_existing": True}

            @declared_attr
            def embedding(cls) -> Mapped[List[float]]:
                return mapped_column("embedding", Vector(self.dimension), nullable=False)

        return CustomCollectionTable

    async def insert(self, id: str, embedding: List[float], metadata: Dict[str, Any] = {}) -> None:
        async with self.session_maker() as session:
            await self.table.create(
                session=session, id=id, embedding=embedding, metadata=metadata
            )

    async def create(self) -> None:
        pass

    async def delete(self, id: str) -> None:
        async with self.session_maker() as session:
            await self.table.delete(session=session, id=id)

    async def query(self, query: List[float], limit: int = 10) -> List[CollectionPointResult]:
        if self.table is None:
            return []

        stmt = select(self.table).order_by(self.table.embedding.cosine_distance(query))
        # add column with cosine similarity
        stmt = stmt.column((1-self.table.embedding.cosine_distance(query)).label("cosine_similarity"))
        stmt = stmt.limit(limit)
        async with self.session_maker() as session:
            query_execution = await session.execute(stmt)
            ## After adding column cosine_similarity to stmt, the result is a tuple of (CollectionTable, cosine_similarity)
            results = query_execution.all()

        return [
            CollectionPointResult(
                id=result[0].id,
                embedding=result[0].embedding,
                metadata=result[0].metadatas,
                score=result[1],
            )
            for result in results
        ]

    async def get(self, id: str) -> CollectionPoint:
        # Get collection point with the given id
        async with self.session_maker() as session:
            result = await self.table.read_by_id(session=session, point_id=id)
            if result is None:
                raise Exception(f"Point with id {id} does not exist")
            return CollectionPoint(
                id=result.id, embedding=result.embedding, metadata=result.metadatas
            )

    async def update(self, id: str, embedding: List[float], metadata: Dict[str, Any] = {}) -> None:
        # Update collection point with the given id
        async with self.session_maker() as session:
            if self.table is not None:
                await self.table.update(session=session, id=id, embedding=embedding, metadata=metadata)

    async def upsert(self, id: str, embedding: List[float], metadata: Dict[str, Any] = {}) -> None:
        ## I want to add some logic to insert data but if the id already exists, then update it
        try:
            await self.insert(id, embedding, metadata)
        except Exception as e:
            if is_duplicate_key_error(e.args[0]):
                await self.update(id, embedding, metadata)
            else:
                raise e

def is_duplicate_key_error(error_message):
    return "duplicate key value violates unique constraint" in error_message
