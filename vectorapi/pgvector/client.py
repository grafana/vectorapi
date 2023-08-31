
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

# from pgvector.asyncpg import register_vector
from pydantic import BaseSettings, PostgresDsn, validator

# from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel, create_engine
from sqlalchemy import Table, Column


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
    SQLALCHEMY_DATABASE_URL: PostgresDsn | None

    @validator("SQLALCHEMY_DATABASE_URL", pre=True)
    def assemble_db_connection_string(cls, v: PostgresDsn | None, values: dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values["POSTGRES_USER"],
            password=values["POSTGRES_PASSWORD"],
            host=values["POSTGRES_HOST"],
            port=values["POSTGRES_PORT"],
            path=f"/{values['POSTGRES_DB']}",
        )

    class Config:
        case_sensitive = True

# class Collection(Table):
#     """Doc here"""
#     __tablename__ = "collection"
#     id = Column(int, primary_key=True)
#     name = Column(str)
#     dimension = Column(int)
#     metric = Column(str)
#     metadata = Column(dict)

class Client:
    """Doc here"""
    def __init__(self, settings=Settings()) -> None:
        """ Create a postgres connection """
        self.engine = AsyncEngine(create_engine(settings.SQLALCHEMY_DATABASE_URL, echo=True, future=True))

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(SQLModel.metadata.create_all)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        try:
            async_session = sessionmaker(
                self.engine,
                class_=AsyncSession,  # type: ignore
                expire_on_commit=False,
            )
            # async_session = async_session_generator()
            async with async_session() as session:
                # await register_vector(session)
                yield session
        except:
            await session.rollback()
            raise
        finally:
            await session.close()

    def create_collection(self, table_name: str) -> None:
        """ Create a new vector collection 
        
        Args:
            name (str): Name of the collection
            dimension (int): Dimension of the vectors in the collection

        Returns:
            Collection: A collection object    
        """
        
        pass