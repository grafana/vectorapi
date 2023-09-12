import os
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, validator

from typing import Any

SCHEMA_NAME = os.getenv("POSTGRES_SCHEMA_NAME", "vector")


class Settings(BaseSettings):
    # PostgreSQL Database Connection
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "0000")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "postgres")
    ECHO_SQL: bool = True
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

settings = Settings()