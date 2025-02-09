from typing import Any, Dict, Optional
from fastapi import HTTPException
from app.core.logging import logger

class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        message: str,
        details: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(
            status_code=status_code,
            detail={
                'message': message,
                'details': details
            }
        )
        self.headers = headers
        logger.error(
            f"Application exception: {message}",
            extra={'details': details}
        )

class DatabaseException(AppException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            status_code=500,
            message=f"Database error: {message}",
            details=details
        )

class ValidationException(AppException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            status_code=422,
            message=f"Validation error: {message}",
            details=details
        )

class AuthenticationException(AppException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            status_code=401,
            message=f"Authentication error: {message}",
            details=details,
            headers={'WWW-Authenticate': 'Bearer'}
        )

class AuthorizationException(AppException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            status_code=403,
            message=f"Authorization error: {message}",
            details=details
        ) 