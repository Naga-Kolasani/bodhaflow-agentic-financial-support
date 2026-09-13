from typing import Literal

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
