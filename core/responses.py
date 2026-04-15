import functools
from typing import Any, Optional, Union, List, Callable, Type
from io import BytesIO
from fastapi import status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

# from core.logger import get_logger

# logger = get_logger()

INTERNAL_ERROR_MSG = "An error occurred. Please contact the administrator."


# --- Response Model ---

class APIResponse(BaseModel):
    message: str
    status: int
    hasError: bool
    data: Optional[Any] = None
    errors: Optional[List[Any]] = None

    # Optional file fields
    file: Optional[bytes] = Field(default=None, exclude=True)
    filename: Optional[str] = Field(default=None, exclude=True)
    byte_data: Optional[bytes] = Field(default=None, exclude=True)

    def to_json_response(self) -> Union[JSONResponse, StreamingResponse]:
        """Convert to FastAPI Response"""

        # 1. Handle File Download
        if self.file:
            return StreamingResponse(
                BytesIO(self.file),
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename={self.filename}"},
            )

        # 2. Handle Raw Bytes
        if self.byte_data:
            from starlette.responses import Response
            return Response(content=self.byte_data, media_type="application/x-protobuf")

        # 3. Standard JSON
        content = self.model_dump(exclude={"file", "filename", "byte_data"})
        return JSONResponse(
            content=jsonable_encoder(content),
            status_code=self.status
        )


# --- Builder Helper ---

def create_response(
    message: str = "",
    data: Any = None,
    errors: Optional[List[str]] = None,
    status_code: int = 200,
    has_error: Optional[bool] = None,
    **kwargs
) -> APIResponse:
    """
    Helper to build APIResponse.
    Auto-detects hasError if not provided.
    For 500 errors, uses the generic INTERNAL_ERROR_MSG unless message is explicitly provided.
    """
    if has_error is None:
        has_error = status_code >= 400

    # For 500 errors, use generic message if not explicitly provided
    if not message:
        if status_code >= 500:
            message = INTERNAL_ERROR_MSG
        elif has_error:
            message = "An error occurred"
        else:
            message = "Successful"

    # Normalize errors to list
    if errors and not isinstance(errors, list):
        errors = [errors]

    return APIResponse(
        message=message,
        status=status_code,
        hasError=has_error,
        data=data,
        errors=errors,
        **kwargs
    )


# --- Route Decorator for Automatic Exception Handling ---

def api_route(
    success_message: str = "Successful",
    response_model: Type[BaseModel] = None,
):
    """
    Decorator that wraps route handlers with automatic exception handling.

    Usage:
        @router.post("")
        @api_route(success_message="User created successfully", response_model=UserResponse)
        async def create_user(...):
            return await service.create_user(...)  # Returns SQLAlchemy model or dict
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)

                # If result is already an APIResponse or JSONResponse, return it directly
                if isinstance(result, (APIResponse, JSONResponse, StreamingResponse)):
                    return result

                # Convert to response model if provided
                if response_model and hasattr(result, "__table__"):
                    result = response_model.model_validate(result)
                elif response_model and isinstance(result, dict):
                    result = response_model.model_validate(result)

                # Convert Pydantic models to dict for serialization
                if isinstance(result, BaseModel):
                    result = result.model_dump()

                return create_response(
                    data=result,
                    message=success_message
                ).to_json_response()

            except Exception as e:
                # Lazy import to avoid circular dependency
                from core.exceptions import CustomException
                if isinstance(e, CustomException):
                    raise
                # logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                return create_response(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                ).to_json_response()

        return wrapper
    return decorator
