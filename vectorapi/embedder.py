import requests

from functools import lru_cache
from typing import List

import numpy as np
import opentelemetry.trace
import torch
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer

from vectorapi.const import DEFAULT_EMBEDDING_MODEL


def get_torch_device() -> str:
    return (
        "mps"
        if getattr(torch, "has_mps", False)
        else "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )


class Embedder:
    def __init__(
        self,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
        batch_size: int = 32,
        device: str = get_torch_device(),
        normalize_embeddings: bool = True,
    ):
        self.model_name = model_name
        self.model = self._load_model(model_name)
        self.batch_size = batch_size
        self.device = device
        self.normalize_embeddings = normalize_embeddings
        self.dimension: int = 0

    def load_model(self, model_name: str) -> None:
        try:
            self.model = SentenceTransformer(model_name)
            self.dimension: int = self.model.get_sentence_embedding_dimension()
        except requests.exceptions.HTTPError as e:
            # huggingface throws "401 Client Error" when a model doesn't exist
            if "401 Client Error" in e.response.text:
                raise ValueError(f"Model {model_name} not found") from e
            raise e

    @property
    def _trace_attributes(self):
        return {
            "model_name": self.model_name,
            "batch_size": self.batch_size,
            "device": self.device,
            "normalize_embeddings": self.normalize_embeddings,
            "dimension": self.dimension,
        }

    @lru_cache(maxsize=128)
    def encode(self, text: str) -> NDArray[np.float_]:
        tracer = opentelemetry.trace.get_tracer(__name__)
        with tracer.start_as_current_span("Embedder.encode", attributes=self._trace_attributes):
            return self.model.encode(
                text,
                batch_size=self.batch_size,
                device=self.device,
                normalize_embeddings=self.normalize_embeddings,
            )

    def generate_similarity(self, source_sentence: str, sentences: List[str]) -> List[float]:
        source_vector = self.encode(source_sentence)

        similarity_scores: List[float] = []
        for sentence in sentences:
            vector = self.encode(sentence)
            similarity = np.matmul(source_vector, vector.T)
            similarity_scores.append(similarity)
        return similarity_scores


@lru_cache(maxsize=3)
def get_embedder(model_name: str) -> Embedder:
    emb = Embedder(model_name=model_name)
    emb.load_model(model_name)
    return emb
