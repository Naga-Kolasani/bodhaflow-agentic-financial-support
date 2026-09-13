from fastapi import FastAPI

from bodhaflow.api.routes.health import router as health_router
from bodhaflow.core.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings if settings is not None else Settings()
    app = FastAPI(title=resolved_settings.app_name, debug=resolved_settings.debug)
    app.include_router(health_router)
    return app


app = create_app()
