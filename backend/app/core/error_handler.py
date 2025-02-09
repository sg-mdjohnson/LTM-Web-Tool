from typing import Any, Dict, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger
from app.core.errors import AppError
from app.core.context import RequestContext

class ErrorHandler:
    @staticmethod
    def handle_error(
        request: Request,
        error: Exception,
        status_code: int = 500,
        error_code: Optional[str] = None
    ) -> JSONResponse:
        context = RequestContext.get_current()
        
        error_response = {
            'success': False,
            'message': str(error),
            'request_id': context.request_id,
            'path': str(request.url),
            'method': request.method,
            'timestamp': context.get_tag('start_time')
        }

        if error_code:
            error_response['error_code'] = error_code

        if isinstance(error, AppError):
            error_response['details'] = error.details
            status_code = error.status_code

        logger.error(
            f"Request failed: {str(error)}",
            extra={
                'request_id': context.request_id,
                'status_code': status_code,
                'error_code': error_code,
                'path': str(request.url),
                'method': request.method
            },
            exc_info=error
        )

        return JSONResponse(
            status_code=status_code,
            content=error_response
        )

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)
            return response
            
        except AppError as e:
            return ErrorHandler.handle_error(
                request,
                e,
                status_code=e.status_code,
                error_code=e.error_code
            )
            
        except Exception as e:
            return ErrorHandler.handle_error(
                request,
                e,
                status_code=500,
                error_code='INTERNAL_ERROR'
            ) 