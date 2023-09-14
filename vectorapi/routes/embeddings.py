"""models.py contains model configuration related apis."""
from typing import List

import fastapi
import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from vectorapi.embedder import get_embedder
from vectorapi.responses import ORJSONResponse

router = fastapi.APIRouter(
    tags=["embeddings"],
)


class BaseModelCamel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)  # type: ignore


class EmbeddingResponseData(BaseModelCamel):
    index: int
    object: str = "embedding"
    embedding: List[float]


class EmbeddingResponseUsage(BaseModelCamel):
    prompt_tokens: int
    total_tokens: int


class EmbeddingResponse(BaseModelCamel):
    object: str = "list"
    data: List[EmbeddingResponseData]
    model: str
    usage: EmbeddingResponseUsage


class EmbeddingRequest(BaseModelCamel):
    model: str = "BAAI/bge-small-en-v1.5"
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
    data = [EmbeddingResponseData(index=0, embedding=vector.tolist())]
    return EmbeddingResponse(
        data=data,
        model=request.model,
        usage=EmbeddingResponseUsage(promptTokens=0, totalTokens=0),
    )


class SimilarityRequest(BaseModelCamel):
    model: str = "BAAI/bge-small-en-v1.5"
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
