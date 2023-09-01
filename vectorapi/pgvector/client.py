
from typing import Any, AsyncGenerator

# from pgvector.asyncpg import register_vector
from pgvector.sqlalchemy import Vector

from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, validator

# from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker, mapped_column
from sqlalchemy.sql import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
# from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.dialects import postgresql
# from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import create_async_engine

from sqlalchemy import Table, Column, String, MetaData


## Create a collection
## Get collections
## Get collection
## Delete a collection
## Update collection (??) 

class Settings(BaseSettings):
    # PostgreSQL Database Connection
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "mysecretpassword"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "postgres"
    SQLALCHEMY_DATABASE_URL: PostgresDsn | None = None

    @validator("SQLALCHEMY_DATABASE_URL", pre=True)
    def assemble_db_connection_string(cls, v: PostgresDsn | None, values: dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values["POSTGRES_USER"],
            password=values["POSTGRES_PASSWORD"],
            host=values["POSTGRES_HOST"],
            port=int(values["POSTGRES_PORT"]),
            path=values['POSTGRES_DB'],
        )

    class Config:
        case_sensitive = True


class Client:
    """Doc here"""
    def __init__(self, settings=Settings()) -> None:
        """ Create a postgres connection """
        self.db_name = settings.POSTGRES_DB
        self.engine = create_async_engine(str(settings.SQLALCHEMY_DATABASE_URL), echo=True, future=True)
        self.async_session = async_sessionmaker(
                self.engine,
                expire_on_commit=False,
            )

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            # await conn.run_sync(SQLModel.metadata.create_all)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.async_session() as session:
            yield session

    async def create_collection(self, name: str, dimension: int) -> None:
        """ Create a new vector collection 
        
        Args:
            name (str): Name of the collection
            dimension (int): Dimension of the vectors in the collection

        Returns:
            Collection: A collection object    
        """
        meta = MetaData(schema=self.db_name)

        collection = Table(
            name,
            meta,
        Column("id", String, primary_key=True),
        Column("vec", Vector(dimension), nullable=False),
        Column(
            "metadata",
            postgresql.JSONB,
            server_default=text("'{}'::jsonb"),
            nullable=False,
        ),
        extend_existing=True,
        )
        
        async with self.engine.begin() as conn:
            await conn.run_sync(meta.drop_all)
            await conn.run_sync(meta.create_all)


class Collection:
    def __init__(self,  name: str, dimension: int) -> None:
        self.table = Table()