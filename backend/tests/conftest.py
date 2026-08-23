# ruff: noqa: E402
from __future__ import annotations

import os

# Environment overrides must be applied before importing application modules.

database_url = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://greenmile:greenmile@localhost:5432/greenmile_test",
)
separator = "&" if "?" in database_url else "?"
if "prepared_statement_cache_size" not in database_url:
    database_url = f"{database_url}{separator}prepared_statement_cache_size=0"
os.environ["DATABASE_URL"] = database_url
os.environ.setdefault("AUTO_SEED_DEMO", "false")

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.db.base import Base
from app.db.session import get_session
from app.main import app

TEST_DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSession = async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def reset_database():
    await engine.dispose()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session_factory():
    return TestSession


@pytest_asyncio.fixture(loop_scope="session")
async def session():
    async with TestSession() as database_session:
        yield database_session


@pytest_asyncio.fixture(loop_scope="session")
async def client():
    async def override_session():
        async with TestSession() as database_session:
            yield database_session

    app.dependency_overrides[get_session] = override_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()
