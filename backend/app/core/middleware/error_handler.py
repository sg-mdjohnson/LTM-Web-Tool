from typing import Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.errors import AppError, AuthenticationError, ValidationError
from app.core.logging import logger
from app.schemas.responses import ErrorResponse
import traceback
import sys

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response

        except AuthenticationError as e:
            logger.warning(f"Authentication error: {str(e)}")
            return self._create_error_response(401, str(e), request)

        except ValidationError as e:
            logger.warning(f"Validation error: {str(e)}")
            return self._create_error_response(422, str(e), request)

        except AppError as e:
            logger.error(f"Application error: {str(e)}")
            return self._create_error_response(400, str(e), request)

        except Exception as e:
            logger.error(
                f"Unhandled error: {str(e)}\n{traceback.format_exc()}",
                exc_info=sys.exc_info()
            )
            return self._create_error_response(
                500,
                "Internal server error",
                request,
                include_details=settings.DEBUG
            )

    def _create_error_response(
        self,
        status_code: int,
        message: str,
        request: Request,
        include_details: bool = False
    ) -> JSONResponse:
        error_response = ErrorResponse(
            message=message,
            request_id=getattr(request.state, 'request_id', None)
        )

        if include_details:
            error_response.details = traceback.format_exc()

        return JSONResponse(
            status_code=status_code,
            content=error_response.dict(exclude_none=True)
        ) 