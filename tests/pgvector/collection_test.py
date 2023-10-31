from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from vectorapi.pgvector.collection import CollectionTable, PGVectorCollection


@pytest.fixture
def mock_sessionmaker():
    # mock instance of async_sessionmaker
    mock_sessionmaker = MagicMock(async_sessionmaker)
    mock_sessionmaker.return_value = AsyncSession
    return mock_sessionmaker


class TestPGVectorCollection:
    def test_init(self, mock_sessionmaker: MagicMock):
        collection = PGVectorCollection(
            name="test_collection",
            dimension=3,
            session_maker=mock_sessionmaker,
        )

        assert isinstance(collection.table, type(CollectionTable))

    def test_serialize(self, mock_sessionmaker: MagicMock):
        collection = PGVectorCollection(
            name="test_collection",
            dimension=3,
            session_maker=mock_sessionmaker,
        )
        collection_json = collection.model_dump()

        # make sure we exclude table and session_maker from the json
        assert "table" not in collection_json.keys()
        assert "session_maker" not in collection_json.keys()
