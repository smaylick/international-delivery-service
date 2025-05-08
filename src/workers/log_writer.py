"""
Слушает RabbitMQ очередь logs_queue и пишет документы в MongoDB.
Запуск внутри контейнера:  python -m src.workers.log_writer
"""

import json
import os
import time

import pika
from pymongo import MongoClient
from pika.exceptions import AMQPConnectionError

RABBIT = os.environ["RABBIT_DSN"]
MONGO = os.environ["MONGO_DSN"]
DBNAME = os.getenv("MONGO_DB", "delivery_logs")

mongo = MongoClient(MONGO)[DBNAME]

params = pika.URLParameters(RABBIT)
params.heartbeat = 0  # не обрывать idle‑коннект

# ─── ждём, когда RabbitMQ станет доступен ─────────────────────────
for attempt in range(1, 31):  # ~1 минуты ожидания
    try:
        conn = pika.BlockingConnection(params)
        break
    except AMQPConnectionError as exc:
        print(
            f"[{attempt:02}/30] RabbitMQ не готов ({exc}); повтор через 2 с", flush=True
        )
        time.sleep(2)
else:
    raise RuntimeError("RabbitMQ так и не ответил за 60 с")

ch = conn.channel()
ch.queue_declare(queue="logs_queue", durable=True)


def callback(_ch, _method, _props, body: bytes):
    mongo.logs.insert_one(json.loads(body))
    _ch.basic_ack(delivery_tag=_method.delivery_tag)


print(" [*] Waiting for logs. To exit press CTRL+C", flush=True)
ch.basic_qos(prefetch_count=50)
ch.basic_consume(queue="logs_queue", on_message_callback=callback)
ch.start_consuming()
