"""Generate local text embeddings without creating an index.

Load the model on the first valid, non-empty request and reuse it
within the same embedder instance.
"""

import numpy as np
from sentence_transformers import SentenceTransformer

from bodhaflow.core.config import Settings


class LocalEmbedder:
    """Generate vectors with the configured local embedding model."""

    def __init__(self, settings: Settings) -> None:
        self._model_name: str = settings.embedding_model
        self._model: SentenceTransformer | None = None

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return normalized vectors in input order without changing the text.

        Return an empty list without loading the model when no texts are given.
        """
        if not texts:
            return []

        _validate_texts(texts)
        model = self._get_model()
        raw_output = model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return _to_validated_vectors(raw_output, expected_rows=len(texts))

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self._model_name, device="cpu")
        return self._model


def _validate_texts(texts: list[str]) -> None:
    for index, text in enumerate(texts):
        if not text.strip():
            raise ValueError(f"texts[{index}] must not be empty or whitespace-only")


def _to_validated_vectors(
    raw_output: object,
    expected_rows: int,
) -> list[list[float]]:
    matrix = np.asarray(raw_output, dtype=np.float64)

    if matrix.ndim != 2:
        raise ValueError(
            "model output must be a two-dimensional matrix, "
            f"got {matrix.ndim} dimensions"
        )

    row_count, dimension = matrix.shape
    if row_count != expected_rows:
        raise ValueError(
            f"model output row count {row_count} "
            f"does not match input count {expected_rows}"
        )
    if dimension <= 0:
        raise ValueError(
            f"model output vector dimension must be positive, got {dimension}"
        )
    if not np.isfinite(matrix).all():
        raise ValueError("model output contains non-finite values")

    return matrix.tolist()
