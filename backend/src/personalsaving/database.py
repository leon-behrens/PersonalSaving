from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from personalsaving.settings import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(url=settings.database_url, pool_pre_ping=True, echo=False)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_db(request: Request) -> AsyncGenerator[AsyncSession]:
    session_factory = request.app.state.session_factory

    async with session_factory() as session:
        yield session
