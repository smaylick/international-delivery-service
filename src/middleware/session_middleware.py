from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import uuid

COOKIE_NAME = "delivery_session"


class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        sid = request.cookies.get(COOKIE_NAME)

        if not sid:
            sid = uuid.uuid4().hex

        request.state.session_id = sid

        response = await call_next(request)

        if not request.cookies.get(COOKIE_NAME):
            response.set_cookie(
                key=COOKIE_NAME,
                value=sid,
                httponly=True,
                max_age=60 * 60 * 24 * 30,
            )

        return response
