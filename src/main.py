# src/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from loguru import logger
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from src.api import api_router
from src.core.logging import setup_logging  # ✨ лог‑конфиг
from src.middleware.request_logging import RequestLoggingMiddleware
from src.middleware.session_middleware import SessionMiddleware
from src.utils.error_handlers import (
    http_exception_handler,
    validation_exception_handler,
    integrity_error_handler,
    generic_exception_handler,
)

# ────────────────────────── логирование ───────────────────────────
setup_logging()  # <‑‑ единственный вызов

# ────────────────────────── middleware ────────────────────────────
middleware = [
    Middleware(SessionMiddleware),
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ),
    Middleware(RequestLoggingMiddleware),  # ↙ наш лог‑мидлвари
]

# ────────────────────────── FastAPI app ───────────────────────────
app = FastAPI(
    title="International Delivery Service",
    middleware=middleware,
)


# ────────────────────────── lifespan ──────────────────────────────
@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("🚀 Application startup")
    yield
    logger.info("🛑 Application shutdown")


app.router.lifespan_context = lifespan

# ────────────────────────── маршруты ──────────────────────────────
app.include_router(api_router)

# ────────────────────────── хэндлеры ошибок ───────────────────────
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# ────────────────────────── root ping ─────────────────────────────
@app.get("/")
def root():
    return {"message": "Hello from Delivery Service"}
