import fastapi
from pydantic import BaseModel
from vectorapi.stores.store_client import StoreClient

router = fastapi.APIRouter(
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
        raise fastapi.HTTPException(
            status_code=500,
            detail=str(e),
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
        raise fastapi.HTTPException(
            status_code=500,
            detail=str(e),
        )
    return fastapi.Response(status_code=204)


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
    except Exception as e:
        raise fastapi.HTTPException(
            status_code=500,
            detail=str(e),
        )
    if collection is None:
        raise fastapi.HTTPException(
            status_code=404,
            detail=f"Collection with name {collection_name} does not exist",
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
    return await client.list_collections()
