# International Delivery Service API

REST API‑сервис для расчёта стоимости международной доставки посылок.  
Стек: **FastAPI & Pydantic / SQLAlchemy (PostgreSQL) / Redis / Celery + RabbitMQ / Docker Compose**.

---

## 🚀 Быстрый старт

### 1  Клонируем репозиторий

```bash
git clone https://github.com/<your‑github>/international-delivery-service.git
cd international-delivery-service
````

### 2 ︎ Переменные окружения

```bash
cp env_example .env.docker
```

### 3  Запуск через Docker Compose 

```bash
docker compose up --build
```

Поднимаются контейнеры: `web` (FastAPI), `db` (PostgreSQL 15), `redis`,
`worker` (Celery + Beat), `rabbit` (RabbitMQ) и `mongo` (MongoDB — хранилище логов).

Доступы:

| Сервис         | URL                                                             |
| -------------- | --------------------------------------------------------------- |
| API            | [http://localhost:8000/](http://localhost:8000/)                |
| Swagger UI     | [http://localhost:8000/docs](http://localhost:8000/docs)        |
| ReDoc          | [http://localhost:8000/redoc](http://localhost:8000/redoc)      |
| RabbitMQ mgmt  | [http://localhost:15672/](http://localhost:15672/) `guest/guest` |
| Mongo Express¹ | [http://localhost:8081/](http://localhost:8081/)  |

---

## ✅ Тесты

```bash
pytest -q 
```
---


## 📚 Документация API

* **Swagger UI** — [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc**       — [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🗄️ Структура проекта

```
international-delivery-service/
│
├── src/
│   ├── api/               # маршруты, Pydantic‑схемы
│   ├── core/              # настройки, Celery, логирование
│   ├── db/                # движки / сессии SQLAlchemy
│   ├── models/            # ORM‑модели
│   ├── services/          # бизнес‑логика, интеграции
│   ├── middleware/        # cookie‑сессии, логирование HTTP
│   └── workers/           # RabbitMQ ➜ MongoDB consumer
│
├── tests/                 # pytest, fakeredis
├── alembic/               # миграции
├── Dockerfile
├── docker-compose.yml
├── env_example            # шаблон переменных
└── README.md
```

---

## 🛠️ Ключевые решения

* **src‑layout** + `poetry` — удобная работа с зависимостями.
* **SQLAlchemy 2.0 async** + *Alembic* миграции.
  Для Celery‑тасок используется синхронный engine.
* **Redis** кэширует курс USD→RUB (`TTL = 1 ч`).
  Данные берутся из JSON ЦБ РФ `https://www.cbr-xml-daily.ru/daily_json.js`.
* **Celery + Beat** (в одном worker’е):

  * обновляет курс каждые 5 минут;
  * массово пересчитывает `delivery_cost_rub` для новых посылок.
* **RabbitMQ** — транспорт логов HTTP‑запросов;
  отдельный consumer пишет их в **MongoDB** (можно анализировать в Grafana/ELK).
* **Cookie‑сессии** (`delivery_session`) — хранит UUID без авторизации.
* Единый формат JSON‑ответов + кастомные обработчики ошибок.
* **Pre‑commit**: `ruff` (линт + авто‑фиксы) и `black` (формат).
  CI легко добавить GitHub Actions‑workflow.