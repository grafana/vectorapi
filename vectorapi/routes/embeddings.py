"""models.py contains model configuration related apis."""
from typing import List

import numpy as np
from fastapi import APIRouter, HTTPException, status
from loguru import logger
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from vectorapi.const import DEFAULT_EMBEDDING_MODEL
from vectorapi.embedder import Embedder, get_embedder
from vectorapi.exceptions import EmbedderModelNotFound
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
    model: str = Field(default=DEFAULT_EMBEDDING_MODEL, min_length=1)
    input: str = Field(min_length=1)
    user: str | None = None


def try_get_embedder(model_name: str) -> Embedder:
    logger.debug(f"Loading embedder for model: {model_name}")
    try:
        embedder = get_embedder(model_name=model_name)
    except EmbedderModelNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"EmbedderModelNotFound: Invalid model name {model_name}, please use a SentenceTransformer compatible model (e.g. {DEFAULT_EMBEDDING_MODEL}): {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading embedder: {e}",
        )
    return embedder


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
    embedder = try_get_embedder(model_name=request.model)
    try:
        vector: NDArray[np.float_] = embedder.encode(request.input)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error encoding text: {e}",
        )
    data = [EmbeddingResponseData(index=0, embedding=vector.tolist())]
    return EmbeddingResponse(
        data=data,
        model=request.model,
        usage=EmbeddingResponseUsage(promptTokens=0, totalTokens=0),
    )


class SimilarityRequest(BaseModelCamel):
    model: str = Field(default=DEFAULT_EMBEDDING_MODEL, min_length=1)
    source_sentence: str = Field(min_length=1)
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
    embedder = try_get_embedder(model_name=request.model)

    try:
        similarity_scores = embedder.generate_similarity(request.source_sentence, request.sentences)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating similarity: {e}",
        )

    return similarity_scores
