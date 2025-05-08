from celery import Celery
from src.core.settings import settings

celery_app = Celery(
    "delivery_service",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    include=[
        "src.tasks",
        "src.services.currency",
        "src.services.delivery",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "update-rate-every-5-min": {
            "task": "src.services.currency.update_rate",
            "schedule": 300,
        },
        "calc-costs-every-5-min": {
            "task": "calculate_delivery_costs",
            "schedule": 300,
        },
    },
)
