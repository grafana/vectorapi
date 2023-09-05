import fastapi
from vectorapi.stores.store_client import StoreClient
from vectorapi.models.collection import CollectionPoint
from loguru import logger
from pydantic import BaseModel
from typing import List

router = fastapi.APIRouter(
    prefix="/collections",
    tags=["collections"],
)


@router.post(
    "/{collection_name}/upsert",
    name="upsert_point",
)
async def upsert_point(
    collection_name: str,
    request: CollectionPoint,
    client: StoreClient,
):
    """Create a new collection with the given name and dimension."""
    try:
        logger.debug(f"Getting collection {collection_name}")
        collection = await client.get_collection(collection_name)
        if collection is None:
            raise fastapi.HTTPException(
                status_code=404,
                detail=f"Collection with name {collection_name} does not exist",
            )
        logger.debug(f"Upserting point {request.id}")
        await collection.upsert(request.id, request.embedding, request.metadata)
    except Exception as e:
        raise fastapi.HTTPException(
            status_code=500,
            detail=str(e),
        )
    return request


@router.delete(
    "/{collection_name}/delete/{point_id}",
    name="delete_point",
)
async def delete_point(
    collection_name: str,
    point_id: str,
    client: StoreClient,
):
    """Delete a collection point with the given id."""
    try:
        logger.debug(f"Getting collection {collection_name}")
        collection = await client.get_collection(collection_name)
        if collection is None:
            raise fastapi.HTTPException(
                status_code=404,
                detail=f"Collection with name {collection_name} does not exist",
            )
        logger.debug(f"Deleting point {point_id}")
        await collection.delete(point_id)
    except Exception as e:
        raise fastapi.HTTPException(
            status_code=500,
            detail=str(e),
        )
    return fastapi.Response(status_code=204)


class QueryPointRequest(BaseModel):
    query: List[float]
    top_k: int = 10


@router.post(
    "/{collection_name}/query",
    name="delete_point",
)
async def query_points(
    collection_name: str,
    request: QueryPointRequest,
    client: StoreClient,
):
    """Delete a collection point with the given id."""
    try:
        logger.debug(f"Getting collection {collection_name}")
        collection = await client.get_collection(collection_name)
        if collection is None:
            raise fastapi.HTTPException(
                status_code=404,
                detail=f"Collection with name {collection_name} does not exist",
            )
        logger.debug(f"Searching {request.top_k} embeddings for query")
        points = await collection.query(request.query, request.top_k)
    except Exception as e:
        raise fastapi.HTTPException(
            status_code=500,
            detail=str(e),
        )
    return points
