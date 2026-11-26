from collections.abc import AsyncGenerator
from typing import cast
from unittest.mock import AsyncMock

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from personalsaving.database import get_db


async def test_health_ok(client: AsyncClient) -> None:
    response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_health_database_unavailable(app: FastAPI, client: AsyncClient) -> None:
    # Failure must happen during execute(), inside the endpoint's try block,
    # rather than while FastAPI resolves the dependency.
    sensitive_details = "host=private-db port=5432 user=secret-user password=secret-password"
    failed_session = AsyncMock(spec=AsyncSession)
    failed_session.execute.side_effect = OSError(sensitive_details)

    async def unavailable_db() -> AsyncGenerator[AsyncSession]:
        yield cast(AsyncSession, failed_session)

    original_override = app.dependency_overrides[get_db]
    app.dependency_overrides[get_db] = unavailable_db
    try:
        response = await client.get("/api/health")
    finally:
        app.dependency_overrides[get_db] = original_override

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert sensitive_details not in response.text
    failed_session.execute.assert_awaited_once()
