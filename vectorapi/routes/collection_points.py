from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Response, status
from loguru import logger
from pydantic import BaseModel

from vectorapi.embedder import get_embedder
from vectorapi.models.collection import CollectionPoint
from vectorapi.routes.collections import get_collection
from vectorapi.stores.store_client import StoreClient

router = APIRouter(
    prefix="/collections",
    tags=["points"],
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
    collection = await get_collection(collection_name, client)

    logger.debug(f"Upserting point {request.id}")
    try:
        await collection.upsert(request.id, request.embedding, request.metadata)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error upserting point: {e}",
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
    collection = await get_collection(collection_name, client)

    logger.debug(f"Deleting point {point_id}")
    try:
        await collection.delete(point_id)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting point: {e}",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{collection_name}/get/{point_id}",
    name="get_point",
)
async def get_point(
    collection_name: str,
    point_id: str,
    client: StoreClient,
):
    """Get the collection point matching the given id."""
    collection = await get_collection(collection_name, client)

    logger.debug(f"Getting collection point {point_id}")
    try:
        return await collection.get(point_id)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting collection point {e}",
        )


class QueryPointRequest(BaseModel):
    query: List[float]
    top_k: int = 10
    filter: Optional[Dict[str, Any]] = None


@router.post(
    "/{collection_name}/query",
    name="query_points",
)
async def query_points(
    collection_name: str,
    request: QueryPointRequest,
    client: StoreClient,
):
    """Query collection with a given embedding query."""
    collection = await get_collection(collection_name, client)

    logger.debug(f"Searching {request.top_k} embeddings for query")
    try:
        points = await collection.query(request.query, request.top_k, request.filter)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching embeddings: {e}",
        )
    return points


class SearchPointRequest(BaseModel):
    input: str
    filter: Optional[Dict[str, Any]] = None
    top_k: int = 10
    model_name: str = "BAAI/bge-small-en-v1.5"


@router.post(
    "/{collection_name}/search",
    name="search",
)
async def search(
    collection_name: str,
    request: SearchPointRequest,
    client: StoreClient,
):
    """Search collection with a given text input."""
    collection = await get_collection(collection_name, client)

    try:
        embedder = get_embedder(model_name=request.model_name)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting embedder: {e}",
        )

    if embedder.dimension != collection.dimension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Embedder dimension {embedder.dimension} does not match collection "
            + f"dimension {collection.dimension}",
        )

    try:
        vector = embedder.encode(request.input)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error encoding text: {e}",
        )

    logger.debug(f"Searching {request.top_k} embeddings for query")
    try:
        points = await collection.query(vector.tolist(), request.top_k, filter=request.filter)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching embeddings: {e}",
        )
    return points
