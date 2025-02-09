from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.errors import AppError
from app.schemas.responses import ErrorResponse
import logging
import traceback
from uuid import uuid4

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid4())
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            return response
            
        except AppError as e:
            logger.warning(
                f"Application error: {str(e)}",
                extra={"request_id": request_id}
            )
            return JSONResponse(
                status_code=e.status_code,
                content=ErrorResponse(
                    message=str(e),
                    request_id=request_id
                ).dict()
            )
            
        except Exception as e:
            logger.error(
                f"Unhandled error: {str(e)}\n{traceback.format_exc()}",
                extra={"request_id": request_id}
            )
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    message="Internal server error",
                    request_id=request_id
                ).dict()
            ) 