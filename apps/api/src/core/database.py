"""SQLAlchemy async engine — Supabase PostgreSQL with production-safe pooling."""

import ssl
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from src.core.config import settings

_connect_args: dict = {}
if settings.database_requires_ssl():
    _connect_args["ssl"] = ssl.create_default_context()

_engine_kwargs: dict = {
    "echo": settings.DEBUG,
    "pool_pre_ping": True,
    "connect_args": _connect_args,
}

if settings.DB_USE_NULL_POOL:
    _engine_kwargs["poolclass"] = NullPool
else:
    _engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    _engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
