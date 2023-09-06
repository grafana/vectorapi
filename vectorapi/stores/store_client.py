import os
from typing import Annotated

from fastapi import Depends

from vectorapi.models.client import Client
from vectorapi.stores.numpy.client import NumpyClient
from vectorapi.stores.pgvector.client import PGVectorClient

VECTORDB_CLIENT = os.environ.get("VECTORDB_CLIENT", "pgvector")


def init_client(client: str) -> Client:
    """init_client returns the client instance."""
    # TODO: Add logic to determine which client to use
    if client == "memory":
        return NumpyClient()
    elif client == "pgvector":
        pg_client = PGVectorClient()
        return pg_client
    else:
        raise NotImplementedError(f"Client {client} not implemented")


client = init_client(VECTORDB_CLIENT)


async def get_client() -> Client:
    return client


StoreClient = Annotated[Client, Depends(get_client)]
