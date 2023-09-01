from fastapi import APIRouter, Depends, Path, Request

from vectorapi.models import CollectionSchema

from .schema import (
    CreateCollectionRequest,
    CreateCollectionResponse,
    ReadAllCollectionResponse,
    ReadCollectionResponse,
    UpdateCollectionRequest,
    UpdateCollectionResponse,
)
from .use_cases import (
    CreateCollection,
    DeleteCollection,
    ReadAllCollection,
    ReadCollection,
    UpdateCollection,
)

router = APIRouter(prefix="/notebooks")


@router.post("", response_model=CreateCollectionResponse)
async def create(
    request: Request,
    data: CreateCollectionRequest,
    use_case: CreateCollection = Depends(CreateCollection),
) -> CollectionSchema:
    return await use_case.execute(data.title, data.notes)


@router.get("", response_model=ReadAllCollectionResponse)
async def read_all(
    request: Request, use_case: ReadAllCollection = Depends(ReadAllCollection)
) -> ReadAllCollectionResponse:
    return ReadAllCollectionResponse(notebooks=[nb async for nb in use_case.execute()])


@router.get(
    "/{notebook_id}",
    response_model=ReadCollectionResponse,
)
async def read(
    request: Request,
    notebook_id: int = Path(..., description=""),
    use_case: ReadCollection = Depends(ReadCollection),
) -> CollectionSchema:
    return await use_case.execute(notebook_id)


@router.put(
    "/{notebook_id}",
    response_model=UpdateCollectionResponse,
)
async def update(
    request: Request,
    data: UpdateCollectionRequest,
    notebook_id: int = Path(..., description=""),
    use_case: UpdateCollection = Depends(UpdateCollection),
) -> CollectionSchema:
    return await use_case.execute(notebook_id, title=data.title, notes=data.notes)


@router.delete("/{notebook_id}", status_code=204)
async def delete(
    request: Request,
    notebook_id: int = Path(..., description=""),
    use_case: DeleteCollection = Depends(DeleteCollection),
) -> None:
    await use_case.execute(notebook_id)
