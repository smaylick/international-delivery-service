# src/core/logging.py
from pathlib import Path
from loguru import logger
import sys
import logging

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def setup_logging():
    """
    • stdout: красивый цветной вывод
    • file:   json‑строки (подойдут для ELK / Loki)
    • перехватываем стандартный logging.*
    """
    logger.remove()  # убираем дефолтный handler

    # → консоль
    logger.add(
        sys.stdout,
        enqueue=True,
        backtrace=True,
        colorize=True,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
    )

    # → файл (JSON)
    logger.add(
        LOG_DIR / "app.log",
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        serialize=True,  # пишет JSON‑строки
        level="INFO",
        backtrace=True,
        enqueue=True,
    )

    # переадресуем стандартный logging → Loguru
    class _Intercept(logging.Handler):
        def emit(self, record):
            logger_opt = logger.bind(request_id="std")
            logger_opt.opt(depth=6, exception=record.exc_info).log(
                record.levelname, record.getMessage()
            )

    logging.basicConfig(handlers=[_Intercept()], level=0)
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = [_Intercept()]
