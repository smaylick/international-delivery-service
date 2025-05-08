import fakeredis
import pytest
from src.services.currency import get_rate, get_rate_sync
from src.services.delivery import calculate_delivery_costs
from src.models.package import Package

# -------------------------------------------------- currency -------------------------------------------


@pytest.mark.asyncio
async def test_get_rate_caches_in_redis(fake_redis):
    """Первый вызов тянет ЦБ и кладёт в кеш; второй берёт из кеша."""
    r1 = await get_rate()
    # должно записаться в Redis
    cached_raw = await fake_redis.get("usd_rub_rate")
    assert float(cached_raw) == pytest.approx(r1)

    # изменим заглушку ЦБ, но из‑за кеша курс не поменяется
    await fake_redis.set("usd_rub_rate", "123.45")
    r2 = await get_rate()
    assert r2 == 123.45


def test_get_rate_sync_uses_cache(fake_redis, _fake_server):
    """Синхронный вариант должен пользоваться тем же ключом."""
    fake_redis_sync = fakeredis.FakeRedis(server=_fake_server)  # тот же сервер
    fake_redis_sync.set("usd_rub_rate", "88.8")
    assert get_rate_sync() == pytest.approx(88.8)


@pytest.mark.asyncio
async def test_calculate_delivery_costs_updates_null(
    async_session, create_package_type
):
    type_id = create_package_type("Books")

    pkg = Package(
        session="test‑session",
        name="Book",
        weight=2.0,  # *0.5 → 1.0
        content_cost_usd=20.0,  # *0.01 → 0.2
        type_id=type_id,
    )
    async_session.add(pkg)
    await async_session.commit()
    await async_session.refresh(pkg)

    # запускаем sync‑таску
    calculate_delivery_costs()

    # получаем свежие данные
    await async_session.refresh(pkg)

    assert pkg.delivery_cost_rub == pytest.approx(120.0)
