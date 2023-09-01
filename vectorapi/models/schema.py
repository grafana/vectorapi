from pydantic import BaseModel, ConfigDict
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql


class CollectionSchema(BaseModel):
    id: int
    embedding: Vector
    metadata: postgresql.JSONB

    model_config = ConfigDict(from_attributes=True)
