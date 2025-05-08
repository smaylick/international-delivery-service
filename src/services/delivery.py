from sqlalchemy import text
from src.core.celery_app import celery_app
from src.services.currency import get_rate_sync
from src.db.session import get_sync_session


@celery_app.task(name="calculate_delivery_costs")
def calculate_delivery_costs() -> None:
    """Заполняет delivery_cost_rub там, где ещё NULL."""
    rate = get_rate_sync()
    session = get_sync_session()
    try:
        session.execute(
            text(
                """
                UPDATE packages
                   SET delivery_cost_rub =
                       (weight * 0.5 + content_cost_usd * 0.01) * :rate
                 WHERE delivery_cost_rub IS NULL
            """
            ),
            {"rate": rate},
        )
        session.commit()
    finally:
        session.close()
