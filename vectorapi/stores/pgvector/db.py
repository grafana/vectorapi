from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from pgvector.utils import from_db_binary, to_db_binary
from vectorapi.stores.pgvector.client_settings import settings
from sqlalchemy import event, AdaptedConnection

from typing import Dict, Any
from sqlalchemy import Table
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql.base import PGInspector


def init_db_engine():
    async_engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URL.unicode_string(),
        pool_pre_ping=True,
        echo=settings.ECHO_SQL,
    )

    @event.listens_for(async_engine.sync_engine, "connect")
    def register_vector(dbapi_connection: AdaptedConnection, *args):
        stmt = "CREATE EXTENSION IF NOT EXISTS vector"
        dbapi_connection.run_async(lambda conn: conn.execute(stmt))

        # dbapi_connection.run_async(
        #     lambda connection: connection.set_type_codec(
        #         "vector", encoder=to_db_binary, decoder=from_db_binary, format="binary"
        #     )
        # )

    @event.listens_for(Table, "column_reflect")
    def _setup_vectortype(inspector: PGInspector, table: Table, column_info: Dict[str, Any]):
        if column_info["name"] == "embedding":
            column_info["type"] = Vector(768)

    bound_async_sessionmaker = async_sessionmaker(
        bind=async_engine,
        autoflush=False,
        future=True,
    )
    return (async_engine, bound_async_sessionmaker)
