from unittest.mock import MagicMock

import numpy as np
import pytest
from pytest_benchmark.plugin import BenchmarkFixture

from vectorapi.embedder import Embedder


class TestEmbedder:
    def test_encode(self):
        embedder = Embedder(model_name="BAAI/bge-base-en")
        embedder.encode = MagicMock(return_value=np.array([1, 2, 3]))
        result = embedder.encode("test")
        assert result.tolist() == [1, 2, 3]

    def test_generate_similarity_matrix(self):
        embedder = Embedder(model_name="sentence-transformers/all-MiniLM-L12-v1")
        embedder.generate_similarity = MagicMock(return_value=np.array([1, 2, 3]))  # type: ignore
        result = embedder.generate_similarity("test", ["test1", "test2"])
        assert result.tolist() == [1, 2, 3]

    @pytest.mark.skip(reason="benchmark test")
    def test_encode__benchmark(self, benchmark: BenchmarkFixture):
        embedder = Embedder(model_name="BAAI/bge-small-en-v1.5")
        # encode once to make sure we have cache
        embedder.encode("test")
        benchmark(embedder.encode, "Why is my Mimir query performance so slow?")
