"""models.py contains model configuration related apis."""
from typing import List

import fastapi
from pydantic import BaseModel

from vectorapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from vectorapi.db import client

router = fastapi.APIRouter(
    prefix="/collections",
    tags=["collections"],
)

class CollectionCreateRequest(BaseModel):
    name: str
    dimension: int


class CollectionCreateResponse(BaseModel):
    success: bool
    errors: List[str] = []

# fastapi Depends is used to inject the client into the request
# This is a dependency injection pattern
@router.post(
    "/create",
    name="create_collection",
    response_model=CollectionCreateResponse,
    response_class=ORJSONResponse,
)
async def create_collection(request: CollectionCreateRequest):
    await client.create_collection(request.name, request.dimension)
    return CollectionCreateResponse(success=True)