import contextlib
import asyncio
import pytest

import fakeredis
import fakeredis.aioredis

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import create_engine, event

from src.main import app
from src.db.base import Base
from src.db.deps import get_async_session


def unwrap(resp):
    assert resp.status_code // 100 == 2, resp.text
    body = resp.json()
    assert body["success"] is True
    return body["data"]


DATABASE_URL = "sqlite+aiosqlite:///file::memory:?cache=shared"

engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,
    connect_args={"uri": True},
)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture(scope="function")
async def async_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture(scope="function", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def test_client(async_session: AsyncSession) -> TestClient:
    app.dependency_overrides[get_async_session] = lambda: async_session
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def create_package_type(test_client: TestClient):
    """
    POST /package-types ➜ возвращает id созданного типа.
    """

    def _create_type(name: str) -> int:
        resp = test_client.post("/package-types", json={"name": name})
        pt = unwrap(resp)
        return pt["id"]

    return _create_type


@pytest.fixture(scope="session")
def _fake_server():
    return fakeredis.FakeServer()


@pytest.fixture(scope="function", autouse=True)
def fake_redis(monkeypatch, _fake_server):
    fake_async = fakeredis.aioredis.FakeRedis(server=_fake_server)
    fake_sync = fakeredis.FakeRedis(server=_fake_server)

    monkeypatch.setattr("src.services.currency.aioredis.Redis", lambda **_: fake_async)
    monkeypatch.setattr("src.services.currency.redis.Redis", lambda **_: fake_sync)
    monkeypatch.setattr(
        "src.services.currency.redis.asyncio.Redis", lambda **_: fake_async
    )

    yield fake_async
    with contextlib.suppress(Exception):
        asyncio.run(fake_async.aclose())
    fake_sync.close()


@pytest.fixture(autouse=True)
def patch_sync_layer(monkeypatch):
    from src.tests.conftest import engine as async_engine

    sync_url = str(async_engine.url).replace("+aiosqlite", "")
    sync_engine = create_engine(
        sync_url,
        connect_args={"uri": True, "check_same_thread": False},
    )
    Base.metadata.create_all(sync_engine)
    SyncSessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)

    monkeypatch.setattr(
        "src.services.delivery.get_sync_session",
        lambda: SyncSessionLocal(),
        raising=True,
    )

    monkeypatch.setattr(
        "src.services.currency.get_rate_sync", lambda: 100.0, raising=True
    )
    monkeypatch.setattr(
        "src.services.delivery.get_rate_sync", lambda: 100.0, raising=True
    )


@event.listens_for(engine.sync_engine, "connect")
def _fk_pragma(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA foreign_keys=ON")
