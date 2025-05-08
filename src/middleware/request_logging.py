import json
import os
import time
import uuid
from datetime import datetime, timezone

import pika
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# ---------- RabbitMQ config -------------------------------------------------
RABBIT_DSN = os.getenv("RABBIT_DSN")  # может быть None во время тестов
_QUEUE = "logs_queue"
_connection = None  # кешируем соединение
_channel = None  # и сам канал


def _get_channel():
    """
    Сингл‑тон‑канал к RabbitMQ. Возвращает None, если подключения нет.
    """
    global _connection, _channel

    if not RABBIT_DSN:  # нет DSN → «немой» режим
        return None

    if _channel and _channel.is_open:
        return _channel

    try:
        params = pika.URLParameters(RABBIT_DSN)
        _connection = pika.BlockingConnection(params)
        _channel = _connection.channel()
        _channel.queue_declare(queue=_QUEUE, durable=True)
        return _channel
    except Exception as exc:  # noqa: BLE001 – любая ошибка ⇒ warning + «немой»
        logger.warning(f"RabbitMQ unavailable — log not sent ({exc})")
        _connection = _channel = None
        return None


def publish_log(payload: dict) -> None:
    """
    Сериализует payload в JSON и отдаёт в очередь.
    Если канал недоступен — молча игнорируем (уже залогировано warning).
    """
    ch = _get_channel()
    if ch is None:
        return

    ch.basic_publish(
        exchange="",
        routing_key=_QUEUE,
        body=json.dumps(payload).encode(),
        properties=pika.BasicProperties(
            delivery_mode=2,  # persistent
            content_type="application/json",
        ),
    )


# ---------- HTTP‑мидлварь ---------------------------------------------------
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Логируем <method path status time> и отправляем JSON‑лог в RabbitMQ.
    """

    async def dispatch(self, request: Request, call_next):
        start_ts = time.perf_counter()
        req_id = uuid.uuid4().hex

        logger.bind(req_id=req_id, method=request.method, path=request.url.path).info(
            "→ incoming request"
        )

        response = await call_next(request)

        duration = (time.perf_counter() - start_ts) * 1000
        logger.bind(
            req_id=req_id, status=response.status_code, duration=f"{duration:.2f} ms"
        ).info("← response sent")

        # -------- отправляем в очередь (не ломаемся при ошибке) -----------
        try:
            payload = {
                "req_id": req_id,
                "ts": datetime.now(tz=timezone.utc).isoformat(),
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round(duration, 2),
            }
            publish_log(payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Log publish failed: {exc}")

        return response
