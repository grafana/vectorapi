from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List
from pydantic import ConfigDict, Field
from pgvector.sqlalchemy import Vector
from sqlalchemy import String, select, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from vectorapi.models.collection import Collection
from vectorapi.models.collection import CollectionPoint, CollectionPointResult
from sqlalchemy.ext.asyncio import async_sessionmaker
from vectorapi.stores.pgvector.base import Base
from typing import Type


class CollectionTable(AbstractConcreteBase, Base):
    __abstract__ = True
    __dimensions__ = 0

    strict_attrs = True
    id: Mapped[str] = mapped_column(
        "id", String, autoincrement=False, nullable=False, unique=True, primary_key=True
    )
    embedding: Mapped[List[float]] = mapped_column(
        "embedding", Vector(__dimensions__), nullable=False
    )
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
    async def read_by_id(
        cls, session: AsyncSession, collection_id: str, include_metadata: bool = False
    ) -> CollectionTable | None:
        stmt = select(cls).where(cls.id == collection_id)
        return await session.scalar(stmt.order_by(cls.id))

    @classmethod
    async def create(
        cls, session: AsyncSession, id: str, embedding: List[float], metadata: Dict[str, Any]
    ) -> CollectionTable:
        collection = CollectionTable(
            id=id,
            embedding=embedding,
            metadata=metadata,
        )
        session.add(collection)
        await session.flush()
        # To fetch metadata
        new = await cls.read_by_id(session, collection.id, include_metadata=True)
        if not new:
            raise RuntimeError()
        return new

    async def update(
        self, session: AsyncSession, embedding: List[float], metadata: Dict[str, Any]
    ) -> None:
        self.embedding = embedding
        self.metadata = metadata
        await session.flush()

    @classmethod
    async def delete(cls, session: AsyncSession, collection: CollectionTable) -> None:
        await session.delete(collection)
        await session.flush()


class PGVectorCollection(Collection):
    session_maker: async_sessionmaker[AsyncSession] = Field(..., exclude=True)
    # table: Type[CollectionTable] = Field(exclude=True)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def table(self) -> CollectionTable:
        # Create the class dynamically
        class CustomCollectionTable(CollectionTable):
            __tablename__ = self.name
            __dimensions__ = self.dimension
            __mapper_args__ = {"polymorphic_identity": self.name, "concrete": True}
            __table_args__ = {"extend_existing": True, "autoload": True}

        return CustomCollectionTable()

    # def sync(self):
    #     table_classname = f"{self.name}CollectionTable"
    #     mydict = {
    #         "__tablename__": self.name,
    #         # "__table_args__": {"autoload": True},
    #         "__dimensions__": self.dimension,
    #     }
    #     self.table = type(table_classname, (CollectionTable,), mydict)

    async def insert(self, id: str, embedding: List[float], metadata: Dict[str, Any] = {}) -> None:
        # Implement pgvector-specific logic to insert a point into the collection
        # You may need to use SQL queries to insert the data
        pass

    async def create(self) -> None:
        pass

        # create_expression = CreateTable(self.table, if_not_exists=True)
        # async with self.session_maker() as session:
        #     await session.execute(create_expression)
        #     await session.commit()

        # async with self.session_maker() as session:

        #     session.add(self.table)
        #     await session.flush()

    async def delete(self) -> None:
        async with self.session_maker() as session:
            await session.delete(self.table)
            await session.flush()

    async def query(self, query: List[float], limit: int = 10) -> List[CollectionPointResult]:
        # Implement pgvector-specific logic to search the collection
        # You may need to use SQL queries to search the data
        return []

    async def get(self, id: str) -> CollectionPointResult:
        # Implement pgvector-specific logic to get a point from the collection
        # You may need to use SQL queries to get the data
        async with self.session_maker() as session:
            result = await self.table.read_by_id(session=session, collection_id=id)
        return result

    async def update(self, id: str, embedding: List[float], metadata: Dict[str, Any] = {}) -> None:
        # Implement pgvector-specific logic to update a point in the collection
        # You may need to use SQL queries to update the data
        pass

    async def upsert(self, id: str, embedding: List[float], metadata: Dict[str, Any] = {}) -> None:
        # Implement pgvector-specific logic to upsert a point in the collection
        # You may need to use SQL queries to upsert the data
        async with self.session_maker() as session:
            await self.table.create(session=session, id=id, embedding=embedding, metadata=metadata)
