from pydantic import BaseModel, Field
from typing import Dict, Any, List
from vectorapi.models import CollectionSchema


class CreateCollectionRequest(BaseModel):
    embedding: List[float] = Field(min_length=0)
    metadata: Dict[str, Any] = Field(min_length=0)


class CreateCollectionResponse(CollectionSchema):
    pass


class ReadCollectionResponse(CollectionSchema):
    pass


class ReadAllCollectionResponse(BaseModel):
    Collections: list[CollectionSchema]


class UpdateCollectionRequest(BaseModel):
    embedding: List[float] = Field(min_length=0)
    metadata: Dict[str, Any] = Field(min_length=0)


class UpdateCollectionResponse(CollectionSchema):
    pass
