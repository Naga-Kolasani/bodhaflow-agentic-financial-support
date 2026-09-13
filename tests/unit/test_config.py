import pytest
from pydantic import ValidationError

from bodhaflow.core.config import Settings
from bodhaflow.main import create_app


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BODHAFLOW_APP_NAME", raising=False)
    monkeypatch.delenv("BODHAFLOW_APP_ENV", raising=False)
    monkeypatch.delenv("BODHAFLOW_DEBUG", raising=False)

    settings = Settings(_env_file=None)

    assert settings.app_name == "BodhaFlow"
    assert settings.app_env == "development"
    assert settings.debug is False


def test_settings_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BODHAFLOW_APP_NAME", "TestBodhaFlow")
    monkeypatch.setenv("BODHAFLOW_APP_ENV", "test")
    monkeypatch.setenv("BODHAFLOW_DEBUG", "true")

    settings = Settings(_env_file=None)

    assert settings.app_name == "TestBodhaFlow"
    assert settings.app_env == "test"
    assert settings.debug is True


def test_settings_invalid_app_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BODHAFLOW_APP_NAME", raising=False)
    monkeypatch.delenv("BODHAFLOW_APP_ENV", raising=False)
    monkeypatch.delenv("BODHAFLOW_DEBUG", raising=False)
    monkeypatch.setenv("BODHAFLOW_APP_ENV", "staging")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_create_app_uses_passed_settings() -> None:
    settings = Settings(_env_file=None, app_name="CustomName", debug=True)

    app = create_app(settings)

    assert app.title == "CustomName"
    assert app.debug is True
