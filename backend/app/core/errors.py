from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

@dataclass
class ErrorDetail:
    """Detailed error information"""
    code: str
    message: str
    field: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)

class AppError(Exception):
    """Base application error"""
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[List[ErrorDetail]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or []

class ValidationError(AppError):
    """Validation error"""
    def __init__(
        self,
        message: str = "Validation error",
        details: Optional[List[ErrorDetail]] = None
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )

class AuthenticationError(AppError):
    """Authentication error"""
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[List[ErrorDetail]] = None
    ):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details
        )

class AuthorizationError(AppError):
    """Authorization error"""
    def __init__(
        self,
        message: str = "Not authorized",
        details: Optional[List[ErrorDetail]] = None
    ):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403,
            details=details
        )

class NotFoundError(AppError):
    """Resource not found error"""
    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[List[ErrorDetail]] = None
    ):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details
        )

class ConflictError(AppError):
    """Resource conflict error"""
    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[List[ErrorDetail]] = None
    ):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details=details
        )

class ErrorHandler:
    """Handles error formatting and response generation"""
    
    @staticmethod
    def format_error(error: Exception) -> Dict[str, Any]:
        """Format error for response"""
        if isinstance(error, AppError):
            error_response = {
                "code": error.code,
                "message": error.message,
                "status": error.status_code
            }
            if error.details:
                error_response["details"] = [
                    {
                        "code": detail.code,
                        "message": detail.message,
                        "field": detail.field,
                        "params": detail.params
                    }
                    for detail in error.details
                ]
            return error_response
        
        return {
            "code": "INTERNAL_ERROR",
            "message": str(error),
            "status": 500
        }

class ErrorMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            return await call_next(request)
            
        except HTTPException as e:
            logger.warning(
                f"HTTP error: {e.detail}",
                extra={"status_code": e.status_code}
            )
            error = AppError(
                message=str(e.detail),
                code="HTTP_ERROR",
                status_code=e.status_code
            )
            return Response(
                content=ErrorHandler.format_error(error),
                status_code=e.status_code,
                media_type="application/json"
            )
            
        except AppError as e:
            logger.error(
                f"Application error: {e.message}",
                extra={
                    "code": e.code,
                    "status_code": e.status_code,
                    "details": e.details
                }
            )
            return Response(
                content=ErrorHandler.format_error(e),
                status_code=e.status_code,
                media_type="application/json"
            )
            
        except Exception as e:
            logger.error(f"Unhandled error: {str(e)}", exc_info=True)
            error = AppError(message="Internal server error")
            return Response(
                content=ErrorHandler.format_error(error),
                status_code=500,
                media_type="application/json"
            ) 