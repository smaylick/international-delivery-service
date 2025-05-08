from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import uuid

COOKIE_NAME = "delivery_session"


class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Получаем сессию из cookies
        sid = request.cookies.get(COOKIE_NAME)

        # Если сессии нет, создаем новую
        if not sid:
            sid = uuid.uuid4().hex

        # Устанавливаем session_id в request.state
        request.state.session_id = sid

        # Получаем ответ от следующей в цепочке обработки функции
        response = await call_next(request)

        # Если сессии не было - добавляем ее в cookies
        if not request.cookies.get(COOKIE_NAME):
            response.set_cookie(
                key=COOKIE_NAME,
                value=sid,
                httponly=True,
                max_age=60 * 60 * 24 * 30,  # 30 дней
            )

        return response
