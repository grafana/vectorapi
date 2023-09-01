from typing import AsyncIterator

from fastapi import HTTPException

from vectorapi.db import AsyncSession
from vectorapi.models import Collection, CollectionSchema


class CreateCollection:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session

    async def execute(self, title: str, notes: list[int]) -> CollectionSchema:
        async with self.async_session.begin() as session:
            exist_notes = [n async for n in Note.read_by_ids(session, note_ids=notes)]
            if len(exist_notes) != len(notes):
                raise HTTPException(status_code=404)
            notebook = await Collection.create(session, title, exist_notes)
            return CollectionSchema.model_validate(notebook)


class ReadAllCollection:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session

    async def execute(self) -> AsyncIterator[CollectionSchema]:
        async with self.async_session() as session:
            async for notebook in Collection.read_all(session, include_notes=True):
                yield CollectionSchema.model_validate(notebook)


class ReadCollection:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session

    async def execute(self, notebook_id: int) -> CollectionSchema:
        async with self.async_session() as session:
            notebook = await Collection.read_by_id(session, notebook_id, include_notes=True)
            if not notebook:
                raise HTTPException(status_code=404)
            return CollectionSchema.model_validate(notebook)


class UpdateCollection:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session

    async def execute(self, notebook_id: int, title: str, notes: list[int]) -> CollectionSchema:
        async with self.async_session.begin() as session:
            notebook = await Collection.read_by_id(session, notebook_id, include_notes=True)
            if not notebook:
                raise HTTPException(status_code=404)

            exist_notes = [n async for n in Note.read_by_ids(session, note_ids=notes)]
            if len(exist_notes) != len(notes):
                raise HTTPException(status_code=404)
            await notebook.update(session, title, exist_notes)
            await session.refresh(notebook)
            return CollectionSchema.model_validate(notebook)


class DeleteCollection:
    def __init__(self, session: AsyncSession) -> None:
        self.async_session = session

    async def execute(self, notebook_id: int) -> None:
        async with self.async_session.begin() as session:
            notebook = await Collection.read_by_id(session, notebook_id)
            if not notebook:
                return
            await Collection.delete(session, notebook)
