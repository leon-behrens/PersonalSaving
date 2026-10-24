import logging
from importlib.metadata import version

from fastapi import FastAPI

from personalsaving.api.health import router as health_router
from personalsaving.api.v1.router import router as v1_router
from personalsaving.logging_config import configure_logging
from personalsaving.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)
    logger = logging.getLogger(__name__)

    logger.info("Starting environment=%s", settings.environment_name)

    servers = [{"url": settings.external_base_url}]

    app = FastAPI(title="PersonalSaving", version=version("personalsaving"), servers=servers)

    app.include_router(health_router, prefix="/api", tags=["health"])

    app.include_router(v1_router, prefix="/api/v1")

    logger.info("App version=%s", app.version)

    return app
