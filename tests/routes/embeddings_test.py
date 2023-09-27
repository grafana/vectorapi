from unittest.mock import Mock, patch

import numpy as np
import pytest
from httpx import AsyncClient

from vectorapi import main
from vectorapi.embedder import Embedder
from vectorapi.routes.embeddings import (
    EmbeddingRequest,
    EmbeddingResponse,
    SimilarityRequest,
)

pytestmark = pytest.mark.asyncio

np.random.seed(42)


class MockEmbedder(Embedder):
    def encode(self, text):
        return np.random.random(3)


# path embedder.encode
@patch("vectorapi.routes.embeddings.get_embedder")
async def test_embeddings(get_embedder_mock: Mock):
    get_embedder_mock.return_value = MockEmbedder()
    embedding_request = EmbeddingRequest(input="foo")

    app = main.create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/v1/embeddings", content=embedding_request.model_dump_json())

    assert response.status_code == 200
    embedding_response = EmbeddingResponse.model_validate_json(response.content)
    assert len(embedding_response.data[0].embedding) == 3


@patch("vectorapi.routes.embeddings.get_embedder")
async def test_similarity(get_embedder_mock: Mock):
    get_embedder_mock.return_value = MockEmbedder()
    similarity_request = SimilarityRequest(
        model="sentence-transformer", sourceSentence="foo", sentences=["bar", "baz"]
    )

    app = main.create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/v1/similarity", content=similarity_request.model_dump_json(by_alias=True)
        )

    assert response.status_code == 200
