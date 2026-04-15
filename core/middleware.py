from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
# from core.logger import get_logger, set_request_id
import uuid


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to each request"""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        # set_request_id(request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
