import fastapi
from vectorapi.stores.store_client import StoreClient
from vectorapi.models.collection import CollectionPoint


router = fastapi.APIRouter(
    prefix="/points",
    tags=["points"],
)


# @router.put(
#     "/{collection_name}",
#     name="upsert_points",
# )
# async def upsert_points(
#     collection_name: str,
#     request: CollectionPoint,
#     client: StoreClient,
# ):
#     """Create a new collection with the given name and dimension."""
#     try:
#         collection = await client.get_collection(collection_name)
#         if collection is None:
#             raise fastapi.HTTPException(
#                 status_code=404,
#                 detail=f"Collection with name {collection_name} does not exist",
#             )
#         await collection.upsert(request.id, request.embedding, request.metadata)
#     except Exception as e:
#         raise fastapi.HTTPException(
#             status_code=500,
#             detail=str(e),
#         )
#     return fastapi.Response(status_code=204)


# class DeleteCollectionRequest(BaseModel):
#     name: str


# @router.post(
#     "/delete",
#     name="delete_collection",
# )
# async def delete_collection(
#     request: DeleteCollectionRequest,
#     client: StoreClient,
# ):
#     """Delete a collection with the given name."""
#     try:
#         await client.delete_collection(request.name)
#     except Exception as e:
#         raise fastapi.HTTPException(
#             status_code=500,
#             detail=str(e),
#         )
#     return fastapi.Response(status_code=204)


# @router.get(
#     "/{collection_name}/points/{point_id}",
#     name="get_collection",
# )
# async def get_collection(
#     collection_name: str,
#     point_id: str,
#     client: StoreClient,
# ):
#     """Get a collection with the given name."""
#     try:
#         collection = await client.get_collection(collection_name)
#     except Exception as e:
#         raise fastapi.HTTPException(
#             status_code=500,
#             detail=str(e),
#         )
#     if collection is None:
#         raise fastapi.HTTPException(
#             status_code=404,
#             detail=f"Collection with name {collection_name} does not exist",
#         )

#     return await collection.get(point_id)


# @router.get(
#     "",
#     name="list_collections",
# )
# async def list_collections(
#     client: StoreClient,
# ):
#     """List all collections."""
#     return await client.list_collections()
