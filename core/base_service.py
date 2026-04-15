from typing import Optional, Any
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from contextvars import ContextVar

# Context variable to store the current request
request_context: ContextVar[Optional[Request]] = ContextVar(
    "request_context", default=None)


class BaseService:
    """
    Base service class that provides request context to all services.
    All services should inherit from this class to get access to the request context.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._request: Optional[Request] = None

    @property
    def request(self) -> Optional[Request]:
        """Get the current request from context."""
        return request_context.get()

    @property
    def current_user(self) -> Optional[Any]:
        """Get the current user from request state if available."""
        if self.request and hasattr(self.request.state, "user"):
            return self.request.state.user
        return None
