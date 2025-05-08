from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder  # 🆕
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from loguru import logger


def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        f"HTTPException → {exc.status_code} {request.method} {request.url.path} – {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            {
                "success": False,
                "message": exc.detail,
                "details": [],
            }
        ),
    )


def validation_exception_handler(request: Request, exc: ValidationError):
    logger.warning(
        f"ValidationError → {request.method} {request.url.path} – fields={[e['loc'][-1] for e in exc.errors()]}"
    )
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(
            {
                "success": False,
                "message": "Validation Error",
                "details": [
                    {"field": e["loc"][-1], "message": e["msg"]} for e in exc.errors()
                ],
            }
        ),
    )


def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.error(f"IntegrityError → {request.method} {request.url.path} – {exc.orig}")
    return JSONResponse(
        status_code=400,
        content=jsonable_encoder(
            {
                "success": False,
                "message": "Database Integrity Error",
                "details": [{"message": str(exc)}],
            }
        ),
    )


def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception → {request.method} {request.url.path}")
    return JSONResponse(
        status_code=500,
        content=jsonable_encoder(
            {
                "success": False,
                "message": "Internal Server Error",
                "details": [{"message": str(exc)}],
            }
        ),
    )
