from __future__ import annotations

from typing import TYPE_CHECKING, AsyncIterator

from sqlalchemy import String, select, text, Column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload
from sqlalchemy.dialects import postgresql
from typing import List, Dict, Any
from .base import Base
from pgvector.sqlalchemy import Vector
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.orm import DeclarativeBase


class Collection(AbstractConcreteBase, DeclarativeBase):
    strict_attrs = True

    id: Mapped[int] = mapped_column(
        "id", autoincrement=True, nullable=False, unique=True, primary_key=True
    )
    embedding: Mapped[List[float]] = mapped_column("embedding", Vector(768), nullable=False)
    metadata: Mapped[Dict[str, Any]] = mapped_column(
        "metadata",
        postgresql.JSONB,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )

    @classmethod
    async def read_all(
        cls, session: AsyncSession, include_metadata: bool
    ) -> AsyncIterator[Collection]:
        stmt = select(cls)
        stream = await session.stream_scalars(stmt.order_by(cls.id))
        async for row in stream:
            yield row

    @classmethod
    async def read_by_id(
        cls, session: AsyncSession, collection_id: int, include_metadata: bool = False
    ) -> Collection | None:
        stmt = select(cls).where(cls.id == collection_id)
        return await session.scalar(stmt.order_by(cls.id))

    @classmethod
    async def create(
        cls, session: AsyncSession, embedding: List[float], metadata: Dict[str, Any]
    ) -> Collection:
        collection = Collection(
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
    async def delete(cls, session: AsyncSession, collection: Collection) -> None:
        await session.delete(collection)
        await session.flush()
