from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BODHAFLOW_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "BodhaFlow"
    app_env: Literal["development", "test", "production"] = "development"
    debug: bool = False
    chroma_path: Path = Path("data/chroma")
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    @field_validator("embedding_model")
    @classmethod
    def embedding_model_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("embedding_model must not be empty or whitespace-only")
        return stripped
