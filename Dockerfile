FROM python:3.11-slim

WORKDIR /app

# Устанавливаем netcat (openbsd), Poetry и зависимости
COPY pyproject.toml poetry.lock ./
RUN apt-get update \
    && apt-get install -y netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip \
    && pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-root

# Копируем код и делаем entrypoint исполняемым
COPY . .
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["web"]
