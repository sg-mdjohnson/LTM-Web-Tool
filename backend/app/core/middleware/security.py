from typing import List
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.schemas.responses import ErrorResponse

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed_hosts: List[str] = None):
        super().__init__(app)
        self.allowed_hosts = allowed_hosts or settings.ALLOWED_HOSTS
        self.security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': self._build_csp_header(),
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }

    def _build_csp_header(self) -> str:
        return "; ".join([
            "default-src 'self'",
            "img-src 'self' data: https:",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline'",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'"
        ])

    async def dispatch(self, request: Request, call_next):
        # Host validation
        host = request.headers.get('host', '').split(':')[0]
        if host not in self.allowed_hosts:
            logger.warning(f"Invalid host header: {host}")
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    message="Invalid host header",
                    detail="This host is not allowed to access the API"
                ).dict()
            )

        response = await call_next(request)

        # Add security headers
        for header_name, header_value in self.security_headers.items():
            response.headers[header_name] = header_value

        return response 