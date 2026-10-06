from pathlib import Path

import pytest
from pydantic import ValidationError

from bodhaflow.core.config import Settings
from bodhaflow.main import create_app


def _clear_bodhaflow_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BODHAFLOW_APP_NAME", raising=False)
    monkeypatch.delenv("BODHAFLOW_APP_ENV", raising=False)
    monkeypatch.delenv("BODHAFLOW_DEBUG", raising=False)
    monkeypatch.delenv("BODHAFLOW_CHROMA_PATH", raising=False)
    monkeypatch.delenv("BODHAFLOW_EMBEDDING_MODEL", raising=False)


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_bodhaflow_env(monkeypatch)

    settings = Settings(_env_file=None)

    assert settings.app_name == "BodhaFlow"
    assert settings.app_env == "development"
    assert settings.debug is False
    assert settings.chroma_path == Path("data/chroma")
    assert settings.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"


def test_settings_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BODHAFLOW_APP_NAME", "TestBodhaFlow")
    monkeypatch.setenv("BODHAFLOW_APP_ENV", "test")
    monkeypatch.setenv("BODHAFLOW_DEBUG", "true")
    monkeypatch.setenv("BODHAFLOW_CHROMA_PATH", "custom/chroma_dir")
    monkeypatch.setenv(
        "BODHAFLOW_EMBEDDING_MODEL",
        "  sentence-transformers/custom-model  ",
    )

    settings = Settings(_env_file=None)

    assert settings.app_name == "TestBodhaFlow"
    assert settings.app_env == "test"
    assert settings.debug is True
    assert settings.chroma_path == Path("custom/chroma_dir")
    assert settings.embedding_model == "sentence-transformers/custom-model"


def test_settings_invalid_app_env(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_bodhaflow_env(monkeypatch)
    monkeypatch.setenv("BODHAFLOW_APP_ENV", "staging")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize("blank_value", ["", "   ", "\t"])
def test_settings_rejects_blank_embedding_model(
    monkeypatch: pytest.MonkeyPatch, blank_value: str
) -> None:
    _clear_bodhaflow_env(monkeypatch)
    monkeypatch.setenv("BODHAFLOW_EMBEDDING_MODEL", blank_value)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_create_app_uses_passed_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_bodhaflow_env(monkeypatch)
    settings = Settings(_env_file=None, app_name="CustomName", debug=True)

    app = create_app(settings)

    assert app.title == "CustomName"
    assert app.debug is True
