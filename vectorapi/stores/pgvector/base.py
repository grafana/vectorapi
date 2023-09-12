from typing import Any, Optional, Sequence as _typing_Sequence, Union
from sqlalchemy import MetaData
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import DeclarativeBase
from vectorapi.stores.pgvector.collection import SCHEMA_NAME
from typing import Sequence

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    __abstract__ = True
    # TODO: Remove ignore
    # https://github.com/sqlalchemy/sqlalchemy/issues/10264
    metadata = MetaData(naming_convention=convention, schema=SCHEMA_NAME)  # type: ignore

    def __repr__(self) -> str:
        columns = ", ".join(
            [f"{k}={repr(v)}" for k, v in self.__dict__.items() if not k.startswith("_")]
        )
        return f"<{self.__class__.__name__}({columns})>"
