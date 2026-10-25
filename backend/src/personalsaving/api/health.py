import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from personalsaving.database import get_db


class HealthResponse(BaseModel):
    status: Literal["ok", "unavailable"]


router = APIRouter()


@router.get(
    "/health",
    responses={
        503: {
            "model": HealthResponse,
            "description": "Database unavailable",
        },
    },
)
async def health(db: Annotated[AsyncSession, Depends(get_db)], response: Response) -> HealthResponse:
    try:
        await db.execute(text("SELECT 1"))
        return HealthResponse(status="ok")
    except (SQLAlchemyError, OSError, TimeoutError) as ex:
        logging.getLogger(__name__).error("Database health check failed: %s", ex)
        response.status_code = 503
        return HealthResponse(status="unavailable")
