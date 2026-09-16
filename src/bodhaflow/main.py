from fastapi import FastAPI

from bodhaflow.api.routes.health import router as health_router
from bodhaflow.core.config import Settings

APP_DESCRIPTION = (
    "BodhaFlow is a fictional, policy-grounded financial support "
    "platform built with synthetic data and mock tools only."
)

OPENAPI_TAGS = [
    {"name": "System", "description": "System health and operational endpoints."},
]


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings if settings is not None else Settings()
    app = FastAPI(
        title=resolved_settings.app_name,
        debug=resolved_settings.debug,
        version="0.1.0",
        description=APP_DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
    )
    app.include_router(health_router)
    return app


app = create_app()
