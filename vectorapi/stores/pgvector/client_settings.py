import os

from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings

SCHEMA_NAME = os.getenv("POSTGRES_SCHEMA_NAME", "vector")


class Settings(BaseSettings):
    # PostgreSQL Database Connection
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "postgres")
    ECHO_SQL: bool = True

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URL(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=int(self.POSTGRES_PORT),
            path=self.POSTGRES_DB,
        )

    class Config:
        case_sensitive = True


settings = Settings()
