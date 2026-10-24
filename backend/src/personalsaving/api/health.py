from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]


router = APIRouter()


@router.get("/health")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
