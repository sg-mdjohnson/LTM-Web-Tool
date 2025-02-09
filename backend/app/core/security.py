from datetime import datetime, timedelta
from typing import Optional, List, Set
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings
from app.core.logging import logger
from app.core.errors import AuthenticationError
from fastapi import FastAPI, Request, Response
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

class SecurityConfig:
    """Security configuration"""
    def __init__(
        self,
        allowed_hosts: List[str] = None,
        allowed_origins: List[str] = None,
        allowed_methods: List[str] = None,
        allowed_headers: List[str] = None,
        expose_headers: List[str] = None,
        max_age: int = 600,
        allow_credentials: bool = True
    ):
        self.allowed_hosts = allowed_hosts or ["*"]
        self.allowed_origins = allowed_origins or ["*"]
        self.allowed_methods = allowed_methods or ["*"]
        self.allowed_headers = allowed_headers or ["*"]
        self.expose_headers = expose_headers or []
        self.max_age = max_age
        self.allow_credentials = allow_credentials

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for handling various security headers and checks"""
    
    def __init__(
        self,
        app: FastAPI,
        config: Optional[SecurityConfig] = None,
        exclude_paths: Optional[Set[str]] = None
    ):
        super().__init__(app)
        self.config = config or SecurityConfig()
        self.exclude_paths = exclude_paths or {
            '/health',
            '/metrics',
            '/docs',
            '/redoc',
            '/openapi.json'
        }
        self.security = HTTPBearer()

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            # Skip security checks for excluded paths
            if request.url.path in self.exclude_paths:
                return await call_next(request)

            # Host validation
            if not self._validate_host(request):
                raise AuthenticationError("Invalid host")

            # Add security headers
            response = await call_next(request)
            return self._add_security_headers(response)

        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}")
            raise

    def _validate_host(self, request: Request) -> bool:
        """Validate request host"""
        if "*" in self.config.allowed_hosts:
            return True

        host = request.headers.get("host", "").split(":")[0]
        return host in self.config.allowed_hosts

    def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response"""
        # CORS headers
        if self.config.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = ",".join(
                self.config.allowed_origins
            )
        if self.config.allowed_methods:
            response.headers["Access-Control-Allow-Methods"] = ",".join(
                self.config.allowed_methods
            )
        if self.config.allowed_headers:
            response.headers["Access-Control-Allow-Headers"] = ",".join(
                self.config.allowed_headers
            )
        if self.config.expose_headers:
            response.headers["Access-Control-Expose-Headers"] = ",".join(
                self.config.expose_headers
            )
        if self.config.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = str(self.config.max_age)

        # Security headers
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": self._get_csp_header(),
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": self._get_permissions_policy()
        })

        return response

    def _get_csp_header(self) -> str:
        """Get Content Security Policy header value"""
        return "; ".join([
            "default-src 'self'",
            "img-src 'self' data: https:",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline'",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ])

    def _get_permissions_policy(self) -> str:
        """Get Permissions Policy header value"""
        return ", ".join([
            "accelerometer=()",
            "camera=()",
            "geolocation=()",
            "gyroscope=()",
            "magnetometer=()",
            "microphone=()",
            "payment=()",
            "usb=()"
        ])

# Example usage:
"""
security_config = SecurityConfig(
    allowed_hosts=settings.ALLOWED_HOSTS,
    allowed_origins=settings.CORS_ORIGINS,
    allowed_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allowed_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Request-ID"],
    max_age=3600,
    allow_credentials=True
)

app.add_middleware(
    SecurityMiddleware,
    config=security_config
)
""" 