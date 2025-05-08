#!/bin/bash
set -e

echo "Waiting for PostgreSQL…"
until nc -z "$DB_HOST" "$DB_PORT"; do sleep 1; done
echo "PostgreSQL is ready!"

# ─── миграции ────────────────────────────────────────────────────────
if [ "$1" = "web" ]; then
  echo "Running Alembic migrations…"
  alembic upgrade head
fi

case "$1" in
  web)
    exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload ;;
  worker)
    exec celery -A src.core.celery_app worker --loglevel=info ;;
  beat)
    exec celery -A src.core.celery_app beat   --loglevel=info ;;
  log_worker)                     # ← новая ветка
    shift                         # убираем слово «log_worker»
    exec python -m src.workers.log_writer "$@" ;;
  *)
    echo "Unknown cmd: $1" && exit 1 ;;
esac
