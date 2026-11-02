"""Store policy sections and explicit embeddings in a local Chroma collection.

Check collection compatibility before updating records. Importing this
module does not initialize a model or open an index.
"""

from collections.abc import Mapping
from pathlib import Path

import chromadb
import numpy as np
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings as ChromaSettings
from chromadb.errors import NotFoundError

from bodhaflow.core.config import Settings
from bodhaflow.rag.embeddings import LocalEmbedder
from bodhaflow.rag.policy_chunks import PolicyChunk, load_policy_chunks

_COLLECTION_NAME = "bodhaflow_policies"
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]
_INDEX_SCHEMA_VERSION = 1
_EMBEDDING_INPUT_VERSION = "title-heading-body-v1"

_Contract = dict[str, str | int | bool]


def build_policy_index(settings: Settings) -> int:
    """Upsert the policy corpus and return the verified record count.

    Do not delete records or roll back failed writes. Reject incompatible
    collections and unexpected record IDs before updating records.
    """
    chunks = _load_validated_chunks()

    embedder = LocalEmbedder(settings)
    vectors = embedder.embed_texts(
        [_format_embedding_input(chunk) for chunk in chunks]
    )
    dimension = _validate_vectors(vectors, expected_rows=len(chunks))

    # Validate the full batch before opening storage.
    contract = _build_contract(settings.embedding_model, dimension)
    client = _open_client(_resolve_storage_path(settings.chroma_path))
    collection = _open_or_create_collection(client, contract)
    _reject_unexpected_ids(collection, chunks)

    collection.upsert(
        ids=[chunk.chunk_id for chunk in chunks],
        documents=[chunk.text for chunk in chunks],
        embeddings=vectors,
        metadatas=[_source_metadata(chunk) for chunk in chunks],
    )

    final_count = collection.count()
    _verify_final_count(final_count, len(chunks))
    return final_count


def _load_validated_chunks() -> list[PolicyChunk]:
    chunks = load_policy_chunks()
    if not chunks:
        raise ValueError("no policy chunks were loaded")

    ids = [chunk.chunk_id for chunk in chunks]
    duplicates = sorted(
        {chunk_id for chunk_id in ids if ids.count(chunk_id) > 1}
    )
    if duplicates:
        raise ValueError(f"duplicate chunk IDs: {duplicates}")
    return chunks


def _format_embedding_input(chunk: PolicyChunk) -> str:
    return f"{chunk.document_title}\n{chunk.section_heading}\n\n{chunk.text}"


def _validate_vectors(vectors: list[list[float]], expected_rows: int) -> int:
    """Validate the embedding batch and return its vector dimension."""
    if len(vectors) != expected_rows:
        raise ValueError(
            f"embedder returned {len(vectors)} vectors for {expected_rows} chunks"
        )

    dimensions = {len(vector) for vector in vectors}
    if len(dimensions) != 1:
        raise ValueError(
            "embedder returned vectors with inconsistent dimensions: "
            f"{sorted(dimensions)}"
        )

    dimension = dimensions.pop()
    if dimension <= 0:
        raise ValueError(
            f"embedding dimension must be positive, got {dimension}"
        )

    if not np.isfinite(np.asarray(vectors, dtype=np.float64)).all():
        raise ValueError("embedder returned non-finite values")
    return dimension


def _resolve_storage_path(chroma_path: Path) -> Path:
    if chroma_path.is_absolute():
        return chroma_path
    return _PROJECT_ROOT / chroma_path


def _build_contract(embedding_model: str, dimension: int) -> _Contract:
    return {
        "index_schema_version": _INDEX_SCHEMA_VERSION,
        "embedding_model": embedding_model,
        "embedding_input_version": _EMBEDDING_INPUT_VERSION,
        "embedding_dimension": dimension,
        "normalize_embeddings": True,
    }


def _open_client(storage_path: Path) -> ClientAPI:
    # Disable Chroma's anonymized telemetry.
    return chromadb.PersistentClient(
        path=str(storage_path),
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def _open_or_create_collection(
    client: ClientAPI,
    contract: _Contract,
) -> Collection:
    try:
        collection = client.get_collection(
            name=_COLLECTION_NAME,
            embedding_function=None,
        )
    except NotFoundError:
        collection = client.create_collection(
            name=_COLLECTION_NAME,
            configuration={"hnsw": {"space": "cosine"}},
            metadata=dict(contract),
            embedding_function=None,
        )
    else:
        _check_contract(collection.metadata, contract)

    _check_cosine_space(collection)
    return collection


def _check_contract(
    metadata: Mapping[str, object] | None,
    contract: _Contract,
) -> None:
    actual = metadata or {}
    problems: list[str] = []
    for key, expected in contract.items():
        if key not in actual:
            problems.append(f"{key} is missing (expected {expected!r})")
        # Require matching types so True cannot match the integer 1.
        elif type(actual[key]) is not type(expected) or actual[key] != expected:
            problems.append(
                f"{key} is {actual[key]!r} (expected {expected!r})"
            )
    if problems:
        raise ValueError(
            f"existing collection {_COLLECTION_NAME!r} "
            "does not match the index contract: "
            + "; ".join(problems)
        )


def _check_cosine_space(collection: Collection) -> None:
    hnsw = collection.configuration.get("hnsw")
    space = hnsw.get("space") if hnsw else None
    if space != "cosine":
        raise ValueError(
            f"collection {_COLLECTION_NAME!r} must use cosine space, "
            f"found {space!r}"
        )


def _reject_unexpected_ids(
    collection: Collection,
    chunks: list[PolicyChunk],
) -> None:
    existing_ids = set(collection.get()["ids"])
    unexpected = sorted(
        existing_ids - {chunk.chunk_id for chunk in chunks}
    )
    if unexpected:
        raise ValueError(
            f"collection {_COLLECTION_NAME!r} has record IDs "
            f"not in the current corpus: {unexpected}"
        )


def _source_metadata(chunk: PolicyChunk) -> dict[str, str]:
    return {
        "source_path": chunk.source_path,
        "document_title": chunk.document_title,
        "section_heading": chunk.section_heading,
    }


def _verify_final_count(actual: int, expected: int) -> None:
    if actual != expected:
        raise RuntimeError(
            f"index verification failed: collection holds {actual} records, "
            f"expected {expected}"
        )
