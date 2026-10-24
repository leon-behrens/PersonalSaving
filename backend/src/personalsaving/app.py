from fastapi import APIRouter, FastAPI

from personalsaving.api.health import router as api_health


def create_app() -> FastAPI:
    app = FastAPI(title="PersonalSaving", version="0.1.0")
    app.include_router(api_health)
    api_v1_router = APIRouter(prefix="/api/v1")
    app.include_router(api_v1_router)
    return app
