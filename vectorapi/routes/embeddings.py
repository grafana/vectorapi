"""models.py contains model configuration related apis."""
from typing import List

import numpy as np
from fastapi import APIRouter, HTTPException, status
from loguru import logger
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from vectorapi.const import DEFAULT_EMBEDDING_MODEL
from vectorapi.embedder import get_embedder
from vectorapi.responses import ORJSONResponse

router = APIRouter(
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
    model: str = DEFAULT_EMBEDDING_MODEL
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

    try:
        embedder = get_embedder(model_name=request.model)
        vector: NDArray[np.float_] = embedder.encode(request.input)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model name {request.model} please use a SentenceTransformer compatible model (e.g. DEFAULT_EMBEDDING_MODEL)",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error encoding text: {e}",
        ) from e
    data = [EmbeddingResponseData(index=0, embedding=vector.tolist())]
    return EmbeddingResponse(
        data=data,
        model=request.model,
        usage=EmbeddingResponseUsage(promptTokens=0, totalTokens=0),
    )


class SimilarityRequest(BaseModelCamel):
    model: str = DEFAULT_EMBEDDING_MODEL
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
    try:
        embedder = get_embedder(model_name=request.model)
        similarity_scores = embedder.generate_similarity(request.source_sentence, request.sentences)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model name {request.model} please use a SentenceTransformer compatible model (e.g. DEFAULT_EMBEDDING_MODEL)",
        ) from e
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating similarity: {e}",
        ) from e

    return similarity_scores
