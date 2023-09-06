"""models.py contains model configuration related apis."""
from functools import lru_cache
from typing import List

import fastapi
import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from vectorapi.embedder import Embedder
from vectorapi.responses import ORJSONResponse

router = fastapi.APIRouter(
    tags=["embeddings"],
)


@lru_cache(maxsize=3)
def get_embedder(model_name: str) -> Embedder:
    return Embedder(model_name=model_name)


class BaseModelCamel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)  # type: ignore


class EmbeddingResponse(BaseModelCamel):
    index: int
    object: str = "embedding"
    embedding: List[float]


class EmbeddingRequest(BaseModelCamel):
    model: str = "BAAI/bge-small-en"
    input: str
    user: str | None = None


@router.post(
    "/embeddings",
    name="create_embeddings",
    response_model=EmbeddingResponse,
    response_class=ORJSONResponse,
)
async def create_embeddings(request: EmbeddingRequest):
    """
    Create embeddings for a given text.
    """
    embedder = get_embedder(model_name=request.model)
    try:
        vector: NDArray[np.float_] = embedder.encode(request.input)
    except Exception as err:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error encoding text: {err}",
        )
    return EmbeddingResponse(index=0, embedding=vector.tolist())


class SimilarityRequest(BaseModelCamel):
    model: str = "BAAI/bge-small-en"
    source_sentence: str
    sentences: List[str]


@router.post(
    "/similarity",
    name="similarity",
    response_model=List[float],
    response_class=ORJSONResponse,
)
async def similarity(request: SimilarityRequest):
    """
    Calculate similarity between two inputs
    """
    embedder = get_embedder(model_name=request.model)

    try:
        similarity_scores = embedder.generate_similarity(request.source_sentence, request.sentences)
    except Exception as err:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error encoding text: {err}",
        )

    return similarity_scores
