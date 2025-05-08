import json
import os
import pika  # синхронно → очень быстрый вызов

_rabbit_conn = pika.BlockingConnection(pika.URLParameters(os.getenv("RABBIT_DSN")))
_channel = _rabbit_conn.channel()
_channel.queue_declare(queue="logs_queue", durable=True)


def publish_log(level: str, message: str, extra: dict | None = None):
    """
    Отправляет лог‑сообщение в RabbitMQ (fire‑and‑forget).
    extra – произвольный JSON‑совместимый словарь
    """
    payload = json.dumps(
        {
            "level": level,
            "message": message,
            "extra": extra or {},
        }
    ).encode()

    _channel.basic_publish(
        exchange="",
        routing_key="logs_queue",
        body=payload,
        properties=pika.BasicProperties(delivery_mode=2),  # persistent
    )
