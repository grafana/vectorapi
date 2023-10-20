from typing import Any, Dict

from loguru import logger
from pgvector.sqlalchemy import Vector
from sqlalchemy import AdaptedConnection, Table, event, text
from sqlalchemy.dialects.postgresql.base import PGInspector
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.schema import CreateSchema

from vectorapi.const import VECTORAPI_STORE_SCHEMA
from vectorapi.pgvector.client_settings import Settings


def init_db_engine(settings: Settings) -> AsyncEngine:
    logger.debug("Connecting to db..")
    async_engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        echo=settings.ECHO_SQL,
    )

    logger.debug("Registering db event listeners..")

    @event.listens_for(async_engine.sync_engine, "connect")
    def register_vector(dbapi_connection: AdaptedConnection, *args):
        # register vector extension
        create_extension = "CREATE EXTENSION IF NOT EXISTS vector"
        dbapi_connection.run_async(lambda conn: conn.execute(create_extension))

        # create schema if it doesn't exist yet
        create_vectordb_schema = CreateSchema(VECTORAPI_STORE_SCHEMA, if_not_exists=True)
        dbapi_connection.run_async(
            lambda conn: conn.execute(create_vectordb_schema.compile().string)
        )

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
                    AND pg_namespace.nspname = '{VECTORAPI_STORE_SCHEMA}'
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

    return async_engine


settings = Settings()
engine = init_db_engine(settings)
bound_async_sessionmaker = async_sessionmaker(
    bind=engine,
    autoflush=False,
    future=True,
)
