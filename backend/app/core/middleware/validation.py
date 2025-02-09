from typing import Callable, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError
from app.core.logging import logger
from app.schemas.responses import ErrorResponse
import uuid

class ValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Validate request content type
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                return JSONResponse(
                    status_code=415,
                    content=ErrorResponse(
                        message="Unsupported Media Type",
                        detail="Content-Type must be application/json",
                        request_id=request_id
                    ).dict()
                )

        try:
            response = await call_next(request)
            return response
        except ValidationError as e:
            logger.warning(
                f"Request validation failed: {str(e)}",
                extra={"request_id": request_id}
            )
            return JSONResponse(
                status_code=422,
                content=ErrorResponse(
                    message="Validation Error",
                    detail=str(e),
                    request_id=request_id
                ).dict()
            )
        except Exception as e:
            logger.error(
                f"Unhandled error in request validation: {str(e)}",
                extra={"request_id": request_id}
            )
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    message="Internal Server Error",
                    request_id=request_id
                ).dict()
            ) 