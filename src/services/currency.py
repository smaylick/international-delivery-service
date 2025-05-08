import logging
import httpx
import requests
import redis
import redis.asyncio as aioredis

from src.core.settings import settings
from src.core.celery_app import celery_app

CBR_URL = "https://www.cbr-xml-daily.ru/daily_json.js"
CACHE_KEY = "usd_rub_rate"
TTL = 60 * 60

logger = logging.getLogger(__name__)


async def _fetch_rate_from_cbr_async() -> float:
    async with httpx.AsyncClient(timeout=5) as client:
        r = await client.get(CBR_URL)
        r.raise_for_status()
        return r.json()["Valute"]["USD"]["Value"]


async def get_rate() -> float:
    """Асинхронный, используется только в FastAPI."""
    r: aioredis.Redis = aioredis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
    )
    try:
        cached = await r.get(CACHE_KEY)
        if cached:
            return float(cached)

        rate = await _fetch_rate_from_cbr_async()
        await r.set(CACHE_KEY, str(rate), ex=TTL)
        return rate
    finally:
        await r.close()


def _fetch_rate_from_cbr_sync() -> float:
    r = requests.get(CBR_URL, timeout=5)
    r.raise_for_status()
    return r.json()["Valute"]["USD"]["Value"]


def get_rate_sync() -> float:
    r = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
    )
    cached = r.get(CACHE_KEY)
    if cached:
        return float(cached)

    rate = _fetch_rate_from_cbr_sync()
    r.set(CACHE_KEY, str(rate), ex=TTL)
    return rate


@celery_app.task(name="src.services.currency.update_rate")
def update_rate() -> None:
    try:
        rate = get_rate_sync()
        logger.info("USD→RUB rate updated to %.4f", rate)
    except Exception as exc:
        logger.error("Failed to update rate: %s", exc)
