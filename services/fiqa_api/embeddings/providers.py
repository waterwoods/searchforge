import os
from typing import List

import numpy as np


class Embedder:
    """Interface for text embedders."""

    def encode(self, texts: List[str]) -> "np.ndarray":  # noqa: F821 (runtime import)
        raise NotImplementedError


class FastEmbedder(Embedder):
    def __init__(self) -> None:
        from fastembed import TextEmbedding

        model_name = os.getenv("FASTEMBED_MODEL", "BAAI/bge-small-en-v1.5")
        try:
            self._model = TextEmbedding(model_name=model_name)
            self.model_name = model_name
        except ValueError as e:
            # Model not supported, fallback to a supported model
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"FastEmbed model '{model_name}' not supported: {e}. Falling back to 'BAAI/bge-small-en-v1.5'")
            self._model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            self.model_name = "BAAI/bge-small-en-v1.5"
        # Get embedding dimension
        try:
            test_vec = list(self._model.embed(["test"]))
            self.dim = len(test_vec[0]) if test_vec else 384
        except Exception:
            self.dim = 384

    def encode(self, texts: List[str]) -> np.ndarray:
        # fastembed returns an iterator of lists
        return np.array(list(self._model.embed(texts)))


class OpenAIEmbedder(Embedder):
    def __init__(self) -> None:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        self._client = OpenAI(api_key=api_key)
        self._model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

    def encode(self, texts: List[str]) -> np.ndarray:
        resp = self._client.embeddings.create(model=self._model, input=texts)
        return np.array([d.embedding for d in resp.data])


class SbertEmbedder(Embedder):
    def __init__(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except Exception as e:  # pragma: no cover - optional path
            raise ImportError(
                f"sentence-transformers not installed: {e}"
            )
        model_name = os.getenv("SBERT_MODEL", os.getenv("ENCODER_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))
        self._model = SentenceTransformer(model_name)
        self.model_name = model_name  # Store model name for consistency checks
        # Get embedding dimension from model
        try:
            # Try to get dimension from model config
            if hasattr(self._model, 'get_sentence_embedding_dimension'):
                self.dim = self._model.get_sentence_embedding_dimension()
            elif hasattr(self._model, 'word_embedding_dimension'):
                self.dim = self._model.word_embedding_dimension
            else:
                # Fallback: encode a test string
                test_vec = self._model.encode(["test"])
                self.dim = len(test_vec[0]) if len(test_vec) > 0 else 384
        except Exception:
            self.dim = 384  # Default for all-MiniLM-L6-v2

    def encode(self, texts: List[str]) -> np.ndarray:
        return np.array(self._model.encode(texts, normalize_embeddings=True))


def get_embedder() -> Embedder:
    backend = os.getenv("EMBEDDING_BACKEND", "FASTEMBED").upper()
    if backend == "OPENAI":
        return OpenAIEmbedder()
    if backend == "SBERT":
        return SbertEmbedder()
    # Default: FASTEMBED (CPU, ONNX)
    return FastEmbedder()


