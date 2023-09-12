from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from vectorapi.stores.pgvector.client_settings import settings, SCHEMA_NAME
from sqlalchemy import event, AdaptedConnection

from typing import Dict, Any
from sqlalchemy import Table, text
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

    @event.listens_for(Table, "column_reflect")
    def _setup_vectortype(inspector: PGInspector, table: Table, column_info: Dict[str, Any]):
        # hacky way to get vector dimensions from the database
        if column_info["name"] == "embedding":
            query = f"""
                SELECT
                    pg_type.typname,
                    pg_attribute.atttypmod
                FROM
                    pg_attribute
                    JOIN pg_class rel ON pg_attribute.attrelid = rel.oid
                    JOIN pg_namespace ON (rel.relnamespace = pg_namespace.oid)
                    JOIN pg_type ON pg_attribute.atttypid = pg_type.oid
                WHERE
                    NOT attisdropped
                    AND pg_attribute.attname = 'embedding'
                    AND rel.relkind = 'r'
                    AND pg_namespace.nspname = '{SCHEMA_NAME}'
                    AND rel.relname = '{table.name}'
                """
            with inspector.engine.begin() as conn:
                result = conn.execute(text(query)).fetchone()
                if result is None:
                    return
                typname, atttypmod = result
                if typname != "vector":
                    return
                column_info["type"] = Vector(atttypmod)

    bound_async_sessionmaker = async_sessionmaker(
        bind=async_engine,
        autoflush=False,
        future=True,
    )
    return (async_engine, bound_async_sessionmaker)
