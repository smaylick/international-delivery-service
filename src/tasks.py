import asyncio
import logging

from src.services.currency import get_rate
from src.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="update_rate")
def update_rate_task() -> None:
    try:
        rate = asyncio.run(get_rate())
        logger.info(f"USD→RUB rate updated to {rate}")
    except Exception as e:
        logger.error(f"Failed to update rate: {e}")
