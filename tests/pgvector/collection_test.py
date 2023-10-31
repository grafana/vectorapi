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
    def test_init(self, mock_sessionmaker):
        collection = PGVectorCollection(
            name="test_collection",
            dimension=3,
            session_maker=mock_sessionmaker,
        )

        assert isinstance(collection.table, type(CollectionTable))
