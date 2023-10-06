from fastapi import APIRouter, HTTPException, Response, status
from loguru import logger
from pydantic import BaseModel

from vectorapi.exceptions import CollectionNotFound
from vectorapi.pgvector.client import StoreClient

router = APIRouter(
    prefix="/collections",
    tags=["collections"],
)


class CreateCollectionRequest(BaseModel):
    collection_name: str
    dimension: int
    exist_ok: bool = False


@router.post(
    "/create",
    name="create_collection",
)
async def create_collection(
    request: CreateCollectionRequest,
    client: StoreClient,
):
    """Create a new collection with the given name and dimension."""
    try:
        if request.exist_ok:
            collection = await client.get_or_create_collection(
                request.collection_name, request.dimension
            )
        else:
            collection = await client.create_collection(request.collection_name, request.dimension)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating collection: {e}",
        )
    return collection


class DeleteCollectionRequest(BaseModel):
    collection_name: str


@router.post(
    "/delete",
    name="delete_collection",
)
async def delete_collection(
    request: DeleteCollectionRequest,
    client: StoreClient,
):
    """Delete a collection with the given name."""
    try:
        await client.delete_collection(request.collection_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting collection {request.collection_name}: {e}",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{collection_name}",
    name="get_collection",
)
async def get_collection(
    collection_name: str,
    client: StoreClient,
):
    """Get a collection with the given name."""
    try:
        collection = await client.get_collection(collection_name)
    except CollectionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection with name {collection_name} does not exist",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting collection {collection_name}: {e}",
        )
    return collection


@router.get(
    "",
    name="list_collections",
)
async def list_collections(
    client: StoreClient,
):
    """List all collections."""
    try:
        return await client.list_collections()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing collections: {e}",
        )
