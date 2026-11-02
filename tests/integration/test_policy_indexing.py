"""Check policy indexing with temporary Chroma storage and a fake embedder.

Compare stored records by ID rather than relying on retrieval order.
Do not load a real model or write to the project's local index.
"""

from collections.abc import Callable
from pathlib import Path
from typing import NoReturn

import chromadb
import numpy as np
import pytest
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings as ChromaSettings

from bodhaflow.core.config import Settings
from bodhaflow.rag import indexing
from bodhaflow.rag.policy_chunks import PolicyChunk, load_policy_chunks

_COLLECTION_NAME = "bodhaflow_policies"
_MODEL_NAME = "test-model"
_DIMENSION = 3
_CONTRACT_FIELDS = (
    "index_schema_version",
    "embedding_model",
    "embedding_input_version",
    "embedding_dimension",
    "normalize_embeddings",
)

Metadata = dict[str, str | int | bool]


def _valid_contract() -> Metadata:
    return {
        "index_schema_version": 1,
        "embedding_model": _MODEL_NAME,
        "embedding_input_version": "title-heading-body-v1",
        "embedding_dimension": _DIMENSION,
        "normalize_embeddings": True,
    }


def _unit_vectors(count: int) -> list[list[float]]:
    vectors: list[list[float]] = []
    for index in range(count):
        raw = np.array([index + 1.0, 1.0, 2.0])
        vectors.append((raw / np.linalg.norm(raw)).tolist())
    return vectors


class _FakeEmbedder:
    def __init__(
        self,
        output_factory: Callable[[int], list[list[float]]] = _unit_vectors,
        error: Exception | None = None,
    ) -> None:
        self._output_factory = output_factory
        self._error = error
        self.calls: list[list[str]] = []

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        if self._error is not None:
            raise self._error
        return self._output_factory(len(texts))


def _refuse_real_embedder(settings: Settings) -> NoReturn:
    raise AssertionError("tests must not construct the real LocalEmbedder")


@pytest.fixture(autouse=True)
def _isolate_indexing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Guard against accidental use of the real model or repository storage.
    monkeypatch.setattr(indexing, "_PROJECT_ROOT", tmp_path / "guard_root")
    monkeypatch.setattr(indexing, "LocalEmbedder", _refuse_real_embedder)


def _install_embedder(
    monkeypatch: pytest.MonkeyPatch,
    output_factory: Callable[[int], list[list[float]]] = _unit_vectors,
    error: Exception | None = None,
) -> _FakeEmbedder:
    fake = _FakeEmbedder(output_factory, error)
    monkeypatch.setattr(indexing, "LocalEmbedder", lambda settings: fake)
    return fake


def _patch_loader(
    monkeypatch: pytest.MonkeyPatch,
    chunks: list[PolicyChunk],
) -> None:
    monkeypatch.setattr(indexing, "load_policy_chunks", lambda: chunks)


def _settings(chroma_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        chroma_path=chroma_path,
        embedding_model=_MODEL_NAME,
    )


def _client(path: Path) -> ClientAPI:
    return chromadb.PersistentClient(
        path=str(path),
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def _get_collection(path: Path) -> Collection:
    return _client(path).get_collection(
        name=_COLLECTION_NAME,
        embedding_function=None,
    )


def _create_collection(
    client: ClientAPI,
    metadata: Metadata | None,
    space: str = "cosine",
) -> Collection:
    return client.create_collection(
        name=_COLLECTION_NAME,
        configuration={"hnsw": {"space": space}},
        metadata=metadata,
        embedding_function=None,
    )


def _seed(
    collection: Collection,
    ids: list[str],
    text: str = "original text",
) -> None:
    collection.upsert(
        ids=ids,
        documents=[text for _ in ids],
        embeddings=[[1.0, 0.0, 0.0] for _ in ids],
    )


def _documents_by_id(collection: Collection) -> dict[str, str]:
    result = collection.get()
    documents = result["documents"]
    assert documents is not None
    return dict(zip(result["ids"], documents, strict=True))


# Check stored policy text, metadata, and vectors.


def test_build_creates_one_record_per_chunk_with_cosine_space(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_embedder(monkeypatch)
    store = tmp_path / "store"

    count = indexing.build_policy_index(_settings(store))

    collection = _get_collection(store)
    assert count == 30
    assert collection.count() == 30
    assert collection.configuration["hnsw"]["space"] == "cosine"
    metadata = collection.metadata
    assert metadata is not None
    for key, expected in _valid_contract().items():
        assert metadata[key] == expected
        assert type(metadata[key]) is type(expected)


def test_stored_records_match_source_chunks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_embedder(monkeypatch)
    store = tmp_path / "store"
    chunks = load_policy_chunks()

    indexing.build_policy_index(_settings(store))

    result = _get_collection(store).get()
    assert result["documents"] is not None
    assert result["metadatas"] is not None
    documents = dict(zip(result["ids"], result["documents"], strict=True))
    metadatas = dict(zip(result["ids"], result["metadatas"], strict=True))
    assert set(documents) == {chunk.chunk_id for chunk in chunks}
    for chunk in chunks:
        assert documents[chunk.chunk_id] == chunk.text
        assert metadatas[chunk.chunk_id] == {
            "source_path": chunk.source_path,
            "document_title": chunk.document_title,
            "section_heading": chunk.section_heading,
        }


def test_supplied_embeddings_are_stored(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_embedder(monkeypatch)
    store = tmp_path / "store"
    chunks = load_policy_chunks()

    indexing.build_policy_index(_settings(store))

    result = _get_collection(store).get(include=["embeddings"])
    stored = result["embeddings"]
    assert stored is not None
    by_id = dict(zip(result["ids"], stored, strict=True))
    for chunk, expected in zip(chunks, _unit_vectors(len(chunks)), strict=True):
        assert np.allclose(by_id[chunk.chunk_id], expected, atol=1e-5)


def test_embedder_receives_exact_inputs_in_loader_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _install_embedder(monkeypatch)
    chunks = load_policy_chunks()

    indexing.build_policy_index(_settings(tmp_path / "store"))

    expected_inputs = [
        f"{chunk.document_title}\n{chunk.section_heading}\n\n{chunk.text}"
        for chunk in chunks
    ]
    assert fake.calls == [expected_inputs]


def test_repeated_build_still_stores_thirty_records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_embedder(monkeypatch)
    store = tmp_path / "store"

    first = indexing.build_policy_index(_settings(store))
    second = indexing.build_policy_index(_settings(store))

    assert (first, second) == (30, 30)
    assert _get_collection(store).count() == 30


def test_updated_text_updates_existing_record_without_duplicates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_embedder(monkeypatch)
    store = tmp_path / "store"
    chunks = load_policy_chunks()
    _patch_loader(monkeypatch, chunks)
    indexing.build_policy_index(_settings(store))

    new_text = "Updated fictional synthetic text for this section."
    updated = [
        chunks[0].model_copy(update={"text": new_text}),
        *chunks[1:],
    ]
    _patch_loader(monkeypatch, updated)
    count = indexing.build_policy_index(_settings(store))

    documents = _documents_by_id(_get_collection(store))
    assert count == 30
    assert len(documents) == 30
    assert documents[chunks[0].chunk_id] == new_text
    assert documents[chunks[1].chunk_id] == chunks[1].text


@pytest.mark.parametrize(
    "seeded_count",
    [0, 2],
    ids=["empty-collection", "partial-collection"],
)
def test_matching_existing_collection_is_filled_to_full_corpus(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    seeded_count: int,
) -> None:
    _install_embedder(monkeypatch)
    store = tmp_path / "store"
    chunks = load_policy_chunks()
    collection = _create_collection(_client(store), _valid_contract())
    if seeded_count:
        _seed(collection, [chunk.chunk_id for chunk in chunks[:seeded_count]])

    count = indexing.build_policy_index(_settings(store))

    documents = _documents_by_id(_get_collection(store))
    assert count == 30
    assert set(documents) == {chunk.chunk_id for chunk in chunks}
    for chunk in chunks[:seeded_count]:
        assert documents[chunk.chunk_id] == chunk.text


def test_new_client_can_read_indexed_records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_embedder(monkeypatch)
    store = tmp_path / "store"
    chunks = load_policy_chunks()
    indexing.build_policy_index(_settings(store))

    reader = _client(store)
    collection = reader.get_collection(
        name=_COLLECTION_NAME,
        embedding_function=None,
    )

    assert collection.count() == 30
    assert set(collection.get()["ids"]) == {chunk.chunk_id for chunk in chunks}


# Check compatibility without overwriting collection metadata.


def test_extra_collection_metadata_is_preserved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_embedder(monkeypatch)
    store = tmp_path / "store"
    metadata = {
        **_valid_contract(),
        "note": "Fictional local test collection",
    }
    _create_collection(_client(store), metadata)

    count = indexing.build_policy_index(_settings(store))

    collection = _get_collection(store)
    assert count == 30
    assert collection.count() == 30
    assert collection.metadata == metadata


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        pytest.param("index_schema_version", 2, id="schema-version"),
        pytest.param("embedding_model", "other-model", id="model-name"),
        pytest.param(
            "embedding_input_version",
            "other-version",
            id="input-version",
        ),
        pytest.param("embedding_dimension", 8, id="dimension"),
        pytest.param(
            "normalize_embeddings",
            False,
            id="normalize-false",
        ),
        pytest.param(
            "normalize_embeddings",
            1,
            id="normalize-int-not-bool",
        ),
    ],
)
def test_mismatched_contract_is_rejected_without_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    bad_value: str | int | bool,
) -> None:
    _install_embedder(monkeypatch)
    store = tmp_path / "store"
    chunks = load_policy_chunks()
    collection = _create_collection(
        _client(store),
        {**_valid_contract(), field: bad_value},
    )
    _seed(collection, [chunks[0].chunk_id])
    metadata_before = dict(collection.metadata or {})
    documents_before = _documents_by_id(collection)

    with pytest.raises(ValueError, match=field):
        indexing.build_policy_index(_settings(store))

    after = _get_collection(store)
    assert dict(after.metadata or {}) == metadata_before
    assert _documents_by_id(after) == documents_before


@pytest.mark.parametrize(
    "missing_field",
    [None, *_CONTRACT_FIELDS],
    ids=["no-metadata", *_CONTRACT_FIELDS],
)
def test_missing_contract_field_is_rejected_without_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    missing_field: str | None,
) -> None:
    _install_embedder(monkeypatch)
    store = tmp_path / "store"
    chunks = load_policy_chunks()
    metadata: Metadata | None
    if missing_field is None:
        metadata = None
    else:
        metadata = {
            key: value
            for key, value in _valid_contract().items()
            if key != missing_field
        }
    collection = _create_collection(_client(store), metadata)
    _seed(collection, [chunks[0].chunk_id])
    metadata_before = dict(collection.metadata or {})
    documents_before = _documents_by_id(collection)

    with pytest.raises(ValueError, match="missing"):
        indexing.build_policy_index(_settings(store))

    after = _get_collection(store)
    assert dict(after.metadata or {}) == metadata_before
    assert _documents_by_id(after) == documents_before


def test_non_cosine_collection_is_rejected_without_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_embedder(monkeypatch)
    store = tmp_path / "store"
    chunks = load_policy_chunks()
    collection = _create_collection(
        _client(store),
        _valid_contract(),
        space="l2",
    )
    _seed(collection, [chunks[0].chunk_id])
    metadata_before = dict(collection.metadata or {})
    documents_before = _documents_by_id(collection)

    with pytest.raises(ValueError, match="cosine"):
        indexing.build_policy_index(_settings(store))

    after = _get_collection(store)
    assert dict(after.metadata or {}) == metadata_before
    assert _documents_by_id(after) == documents_before


def test_unexpected_existing_ids_are_rejected_without_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_embedder(monkeypatch)
    store = tmp_path / "store"
    chunks = load_policy_chunks()
    collection = _create_collection(_client(store), _valid_contract())
    _seed(collection, ["retired:policy_section", chunks[0].chunk_id])
    metadata_before = dict(collection.metadata or {})
    documents_before = _documents_by_id(collection)

    with pytest.raises(ValueError, match="retired:policy_section"):
        indexing.build_policy_index(_settings(store))

    after = _get_collection(store)
    assert dict(after.metadata or {}) == metadata_before
    assert _documents_by_id(after) == documents_before


# Reject invalid inputs before opening storage.


def test_empty_chunk_list_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _install_embedder(monkeypatch)
    _patch_loader(monkeypatch, [])
    store = tmp_path / "store"

    with pytest.raises(ValueError, match="no policy chunks"):
        indexing.build_policy_index(_settings(store))

    assert fake.calls == []
    assert not store.exists()


def test_duplicate_chunk_ids_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _install_embedder(monkeypatch)
    chunks = load_policy_chunks()
    _patch_loader(monkeypatch, [chunks[0], chunks[0]])
    store = tmp_path / "store"

    with pytest.raises(ValueError, match="duplicate chunk IDs"):
        indexing.build_policy_index(_settings(store))

    assert fake.calls == []
    assert not store.exists()


@pytest.mark.parametrize(
    ("output_factory", "message"),
    [
        pytest.param(
            lambda n: _unit_vectors(n - 1),
            "vectors for",
            id="too-few-rows",
        ),
        pytest.param(
            lambda n: _unit_vectors(n + 1),
            "vectors for",
            id="too-many-rows",
        ),
        pytest.param(
            lambda n: [*_unit_vectors(n - 1), [1.0, 0.0]],
            "inconsistent dimensions",
            id="inconsistent-dimensions",
        ),
        pytest.param(
            lambda n: [[] for _ in range(n)],
            "dimension must be positive",
            id="zero-dimension",
        ),
        pytest.param(
            lambda n: [[float("nan"), 0.0, 0.0], *_unit_vectors(n - 1)],
            "non-finite",
            id="nan",
        ),
        pytest.param(
            lambda n: [[float("inf"), 0.0, 0.0], *_unit_vectors(n - 1)],
            "non-finite",
            id="infinity",
        ),
    ],
)
def test_invalid_embeddings_are_rejected_before_any_storage_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    output_factory: Callable[[int], list[list[float]]],
    message: str,
) -> None:
    _install_embedder(monkeypatch, output_factory=output_factory)
    store = tmp_path / "store"

    with pytest.raises(ValueError, match=message):
        indexing.build_policy_index(_settings(store))

    assert not store.exists()


def test_embedder_error_propagates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_embedder(monkeypatch, error=RuntimeError("embedder failed"))
    store = tmp_path / "store"

    with pytest.raises(RuntimeError, match="embedder failed"):
        indexing.build_policy_index(_settings(store))

    assert not store.exists()


# Check path resolution and final count verification.


def test_relative_path_resolves_against_project_root_not_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_embedder(monkeypatch)
    root = tmp_path / "project_root"
    elsewhere = tmp_path / "elsewhere"
    root.mkdir()
    elsewhere.mkdir()
    monkeypatch.setattr(indexing, "_PROJECT_ROOT", root)
    monkeypatch.chdir(elsewhere)

    indexing.build_policy_index(_settings(Path("relative/chroma_store")))

    store = root / "relative" / "chroma_store"
    assert store.is_dir()
    assert any(store.iterdir())
    assert not (elsewhere / "relative").exists()


def test_absolute_path_is_preserved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_embedder(monkeypatch)
    root = tmp_path / "project_root"
    root.mkdir()
    monkeypatch.setattr(indexing, "_PROJECT_ROOT", root)
    store = tmp_path / "absolute_store"

    indexing.build_policy_index(_settings(store))

    assert store.is_dir()
    assert any(store.iterdir())
    assert list(root.iterdir()) == []


def test_final_count_mismatch_raises_runtime_error() -> None:
    with pytest.raises(RuntimeError, match="holds 29 records, expected 30"):
        indexing._verify_final_count(29, 30)
