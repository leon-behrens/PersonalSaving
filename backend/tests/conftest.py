import asyncio
import os
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool, Pool

from personalsaving.app import create_app
from personalsaving.database import get_db
from personalsaving.settings import get_settings


@asynccontextmanager
async def _test_engine(
    url: URL,
    *,
    isolation_level: str = "READ COMMITTED",
    poolclass: type[Pool] = AsyncAdaptedQueuePool,
) -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine(
        url=url,
        isolation_level=isolation_level,
        poolclass=poolclass,
        pool_pre_ping=True,
        echo=False,
    )
    try:
        yield engine
    finally:
        await engine.dispose()


@asynccontextmanager
async def _temporary_database(test_url: URL) -> AsyncGenerator[URL]:
    # The name is generated locally from a fixed prefix and UUID hex characters.
    test_db_name = test_url.database
    admin_url = test_url.set(database="postgres")
    async with _test_engine(admin_url, isolation_level="AUTOCOMMIT", poolclass=NullPool) as admin_engine:
        async with admin_engine.connect() as connection:
            await connection.execute(text(f'CREATE DATABASE "{test_db_name}"'))
        try:
            yield test_url
        finally:
            async with admin_engine.connect() as connection:
                await connection.execute(text(f'DROP DATABASE "{test_db_name}"'))


async def _run_migrations(test_db_name: str) -> None:
    settings = get_settings()
    migration_env = os.environ.copy()
    # Pass the resolved settings too, so the child targets the same server.
    migration_env.update(
        POSTGRES_DB=test_db_name,
        POSTGRES_HOST=settings.postgres_host,
        POSTGRES_PORT=str(settings.postgres_port),
        POSTGRES_USER=settings.postgres_user,
        POSTGRES_PASSWORD=settings.postgres_password.get_secret_value(),
    )
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "alembic",
        "upgrade",
        "head",
        env=migration_env,
        cwd=Path(__file__).resolve().parents[1],
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    # communicate(), not wait(): a piped child can fill the buffer and deadlock.
    output, _ = await process.communicate()
    if process.returncode != 0:
        raise RuntimeError("Test database migrations failed:\n" + output.decode(errors="replace"))


@pytest_asyncio.fixture(scope="session")
async def db_engine() -> AsyncGenerator[AsyncEngine]:
    settings = get_settings()

    # The harness issues CREATE DATABASE and DROP DATABASE against whatever
    # server the environment names. Refuse to do that to a real deployment.
    if settings.environment_name == "production":
        raise RuntimeError(
            "Refusing to run tests against a production configuration: the test "
            "harness creates and drops databases on the configured server."
        )

    test_db_name = f"personalsaving_test_{uuid4().hex}"
    test_url = settings.database_url.set(database=test_db_name)

    async with _temporary_database(test_url):
        await _run_migrations(test_db_name)
        async with _test_engine(test_url) as engine:
            yield engine


@pytest_asyncio.fixture()
async def db_connection(db_engine: AsyncEngine) -> AsyncGenerator[AsyncConnection]:
    async with db_engine.connect() as connection:
        transaction = await connection.begin()
        try:
            yield connection
        finally:
            await transaction.rollback()


@pytest_asyncio.fixture()
async def db_session(db_connection: AsyncConnection) -> AsyncGenerator[AsyncSession]:
    async with AsyncSession(
        bind=db_connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
    ) as session:
        yield session


@pytest.fixture
def app(db_engine: AsyncEngine, db_connection: AsyncConnection, db_session: AsyncSession) -> FastAPI:
    app = create_app()

    # ASGITransport does not run lifespan, so populate the same attributes it
    # would have set. Without this, tests diverge structurally from production
    # and anything reading app.state fails only under test. The factory is
    # bound to the test connection so that sessions created through it join the
    # transaction this test will roll back.
    app.state.engine = db_engine
    app.state.session_factory = async_sessionmaker(
        bind=db_connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    return app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client
