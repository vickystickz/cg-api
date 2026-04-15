# from core.logger import get_logger
from typing import Any, Optional, List
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError, HTTPException
from core.responses import create_response


# --- Base Custom Exception ---

class CustomException(Exception):
    """
    Base class for application exceptions.
    Args:
        message (str): Human readable error message.
        status_code (int): HTTP Status Code.
        errors (List[str]): List of detailed error strings.
        data (Any): Optional data to return in request.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        errors: Optional[List[str]] = None,
        data: Any = None
    ):
        self.message = message
        self.status_code = status_code
        self.errors = errors
        self.data = data
        super().__init__(message)


# --- Specific Exceptions ---

class BadRequestException(CustomException):
    def __init__(self, message: str = "Bad Request", errors: Optional[List[str]] = None):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST, errors=errors)


class NotFoundException(CustomException):
    def __init__(self, message: str = "Resource not found", errors: Optional[List[str]] = None):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND, errors=errors)


class UnauthorizedException(CustomException):
    def __init__(self, message: str = "Unauthorized", errors: Optional[List[str]] = None):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED, errors=errors)


class ForbiddenException(CustomException):
    def __init__(self, message: str = "Forbidden", errors: Optional[List[str]] = None):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN, errors=errors)


class ConflictException(CustomException):
    def __init__(self, message: str = "Resource Conflict", errors: Optional[List[str]] = None):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT, errors=errors)


class UnprocessableEntityException(CustomException):
    def __init__(self, message: str = "Unprocessable Entity", errors: Optional[List[str]] = None):
        super().__init__(message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, errors=errors)


class ServerErrorException(CustomException):
    def __init__(self, message: str = "Internal Server Error", errors: Optional[List[str]] = None):
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, errors=errors)


# --- Exception Handlers ---

async def custom_exception_handler(request: Request, exc: CustomException):
    """Handles our typed CustomExceptions"""
    return create_response(
        message=exc.message,
        errors=exc.errors,
        status_code=exc.status_code,
        data=exc.data
    ).to_json_response()


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handles FastAPI native HTTPExceptions"""
    return create_response(
        message=str(exc.detail),
        errors=[str(exc.detail)],
        status_code=exc.status_code
    ).to_json_response()


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handles Pydantic validation errors"""
    # Format: "loc.path: msg"
    errors = [
        f"{'.'.join(str(x) for x in err['loc'])}: {err['msg']}" for err in exc.errors()]

    return create_response(
        message="Validation Error",
        errors=errors,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    ).to_json_response()


# logger = get_logger()


async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions (500)"""
    # Log the full error with traceback
    # logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)

    return create_response(
        message="An unexpected error occurred. Please contact support.",
        errors=None,  # Hide details
        status_code=500
    ).to_json_response()
