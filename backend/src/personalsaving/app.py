from importlib.metadata import version

from fastapi import FastAPI

from personalsaving.api.health import router as health_router
from personalsaving.api.v1.router import router as v1_router


def create_app() -> FastAPI:
    app = FastAPI(title="PersonalSaving", version=version("personalsaving"))

    app.include_router(health_router, prefix="/api", tags=["health"])

    app.include_router(v1_router, prefix="/api/v1")

    return app
