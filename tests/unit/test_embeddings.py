"""Check local embedding behavior with a fake model.

Replace the model constructor so tests do not download or run a model.
"""

from collections.abc import Callable

import numpy as np
import pytest

from bodhaflow.core.config import Settings
from bodhaflow.rag import embeddings
from bodhaflow.rag.embeddings import LocalEmbedder


def _default_output(sentences: list[str]) -> np.ndarray:
    rows = [[float(index), index + 0.5] for index in range(len(sentences))]
    return np.array(rows, dtype=np.float32)


class _FakeModel:
    def __init__(
        self,
        output_factory: Callable[[list[str]], object] = _default_output,
        encode_error: Exception | None = None,
    ) -> None:
        self._output_factory = output_factory
        self._encode_error = encode_error
        self.encode_calls: list[dict[str, object]] = []

    def encode(self, sentences: list[str], **kwargs: object) -> object:
        self.encode_calls.append({"sentences": sentences, **kwargs})
        if self._encode_error is not None:
            raise self._encode_error
        return self._output_factory(sentences)


class _FakeConstructor:
    def __init__(
        self,
        model: _FakeModel,
        error: Exception | None = None,
    ) -> None:
        self.model = model
        self.error = error
        self.calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def __call__(self, *args: object, **kwargs: object) -> _FakeModel:
        self.calls.append((args, kwargs))
        if self.error is not None:
            raise self.error
        return self.model


def _install_fake(
    monkeypatch: pytest.MonkeyPatch,
    model: _FakeModel | None = None,
    error: Exception | None = None,
) -> _FakeConstructor:
    constructor = _FakeConstructor(
        model if model is not None else _FakeModel(),
        error,
    )
    monkeypatch.setattr(embeddings, "SentenceTransformer", constructor)
    return constructor


def _make_embedder() -> LocalEmbedder:
    return LocalEmbedder(
        Settings(_env_file=None, embedding_model="test-model")
    )


def test_construction_does_not_initialize_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    constructor = _install_fake(monkeypatch)

    _make_embedder()

    assert constructor.calls == []


def test_empty_input_returns_empty_list_without_loading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    constructor = _install_fake(monkeypatch)

    result = _make_embedder().embed_texts([])

    assert result == []
    assert constructor.calls == []


@pytest.mark.parametrize("blank_text", ["", "   "])
def test_blank_text_is_rejected_before_loading(
    monkeypatch: pytest.MonkeyPatch,
    blank_text: str,
) -> None:
    constructor = _install_fake(monkeypatch)

    with pytest.raises(ValueError, match="empty or whitespace-only"):
        _make_embedder().embed_texts([blank_text])

    assert constructor.calls == []


def test_invalid_text_later_in_batch_prevents_model_loading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    constructor = _install_fake(monkeypatch)

    with pytest.raises(ValueError, match=r"texts\[2\]"):
        _make_embedder().embed_texts(["valid one", "valid two", "   "])

    assert constructor.calls == []


def test_model_name_and_cpu_device_reach_constructor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    constructor = _install_fake(monkeypatch)

    _make_embedder().embed_texts(["some text"])

    assert constructor.calls == [(("test-model",), {"device": "cpu"})]


def test_model_is_reused_across_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _FakeModel()
    constructor = _install_fake(monkeypatch, model=model)
    embedder = _make_embedder()

    embedder.embed_texts(["first call"])
    embedder.embed_texts(["second call", "third text"])

    assert len(constructor.calls) == 1
    assert len(model.encode_calls) == 2


def test_inputs_reach_encode_unchanged_and_in_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _FakeModel()
    _install_fake(monkeypatch, model=model)
    texts = ["  padded text  ", "second\n\nwith blank line", "third"]
    expected = list(texts)

    _make_embedder().embed_texts(texts)

    assert model.encode_calls[0]["sentences"] == expected


def test_encode_receives_required_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _FakeModel()
    _install_fake(monkeypatch, model=model)

    _make_embedder().embed_texts(["some text"])

    options = {
        key: value
        for key, value in model.encode_calls[0].items()
        if key != "sentences"
    }
    assert options == {
        "normalize_embeddings": True,
        "convert_to_numpy": True,
        "show_progress_bar": False,
    }


def test_output_is_ordered_plain_lists_of_floats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake(monkeypatch)

    result = _make_embedder().embed_texts(["a", "b", "c"])

    assert result == [[0.0, 0.5], [1.0, 1.5], [2.0, 2.5]]
    assert type(result) is list
    for row in result:
        assert type(row) is list
        for value in row:
            assert type(value) is float


@pytest.mark.parametrize(
    ("bad_output", "message"),
    [
        pytest.param(
            np.array([1.0, 2.0]),
            "two-dimensional",
            id="rank-one",
        ),
        pytest.param(
            np.ones((2, 2, 2)),
            "two-dimensional",
            id="rank-three",
        ),
        pytest.param(
            np.ones((1, 3)),
            "row count",
            id="wrong-row-count",
        ),
        pytest.param(
            np.empty((2, 0)),
            "dimension must be positive",
            id="zero-dimension",
        ),
        pytest.param(
            np.array([[1.0, np.nan], [1.0, 2.0]]),
            "non-finite",
            id="nan",
        ),
        pytest.param(
            np.array([[1.0, 2.0], [np.inf, 2.0]]),
            "non-finite",
            id="infinity",
        ),
    ],
)
def test_malformed_model_output_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    bad_output: np.ndarray,
    message: str,
) -> None:
    model = _FakeModel(output_factory=lambda sentences: bad_output)
    _install_fake(monkeypatch, model=model)

    with pytest.raises(ValueError, match=message):
        _make_embedder().embed_texts(["first", "second"])


def test_model_loading_error_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake(monkeypatch, error=RuntimeError("load failed"))

    with pytest.raises(RuntimeError, match="load failed"):
        _make_embedder().embed_texts(["some text"])


def test_encoding_error_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _FakeModel(encode_error=RuntimeError("encode failed"))
    _install_fake(monkeypatch, model=model)

    with pytest.raises(RuntimeError, match="encode failed"):
        _make_embedder().embed_texts(["some text"])
