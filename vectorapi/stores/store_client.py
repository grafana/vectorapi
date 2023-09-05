import os
from typing import Annotated, AsyncIterator

from fastapi import Depends

from vectorapi.models.client import Client
from vectorapi.stores.numpy.client import get_numpy_client

CLIENT = os.environ.get("CLIENT", "memory")


async def get_client() -> AsyncIterator[Client]:
    """get_client returns the client instance."""
    # TODO: Add logic to determine which client to use
    if CLIENT == "memory":
        yield get_numpy_client()
    else:
        raise NotImplementedError(f"Client {CLIENT} not implemented")


StoreClient = Annotated[Client, Depends(get_client)]
