from typing import Dict, Any, Optional, List, Union, Callable
from enum import Enum
from dataclasses import dataclass
from fastapi import Request, Response, HTTPException, FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.logging import logger

class VersionScheme(str, Enum):
    """API versioning schemes"""
    URL = "url"  # /v1/endpoint
    HEADER = "header"  # X-API-Version: 1.0
    PARAM = "param"  # ?version=1.0
    ACCEPT = "accept"  # Accept: application/vnd.api+json;version=1.0

@dataclass
class APIVersion:
    """API version definition"""
    version: str
    deprecated: bool = False
    deprecated_message: Optional[str] = None
    sunset_date: Optional[str] = None

    def __str__(self) -> str:
        return self.version

    def __lt__(self, other: 'APIVersion') -> bool:
        return (
            self.version < other.version
        )

class VersionManager:
    """Manages API versioning and compatibility"""
    
    def __init__(
        self,
        default_version: str = "1.0",
        scheme: VersionScheme = VersionScheme.URL,
        header_name: str = "X-API-Version",
        param_name: str = "version"
    ):
        self.default_version = default_version
        self.scheme = scheme
        self.header_name = header_name
        self.param_name = param_name
        self._versions: Dict[str, APIVersion] = {}
        self._routes: Dict[str, Dict[str, Callable]] = {}

    def register_version(
        self,
        version: str,
        deprecated: bool = False,
        deprecated_message: Optional[str] = None,
        sunset_date: Optional[str] = None
    ) -> None:
        """Register an API version"""
        self._versions[version] = APIVersion(
            version=version,
            deprecated=deprecated,
            deprecated_message=deprecated_message,
            sunset_date=sunset_date
        )
        self._routes[version] = {}
        logger.info(f"Registered API version: {version}")

    def get_version(self, version: str) -> Optional[APIVersion]:
        """Get version information"""
        return self._versions.get(version)

    def is_deprecated(self, version: str) -> bool:
        """Check if version is deprecated"""
        api_version = self.get_version(version)
        return api_version.deprecated if api_version else False

    def extract_version(self, request: Request) -> str:
        """Extract version from request based on scheme"""
        try:
            if self.scheme == VersionScheme.URL:
                # Extract from URL path: /v1/endpoint
                parts = request.url.path.split('/')
                for part in parts:
                    if part.startswith('v') and part[1:].replace('.', '').isdigit():
                        return part[1:]

            elif self.scheme == VersionScheme.HEADER:
                # Extract from header: X-API-Version: 1.0
                return request.headers.get(self.header_name, self.default_version)

            elif self.scheme == VersionScheme.PARAM:
                # Extract from query param: ?version=1.0
                return request.query_params.get(self.param_name, self.default_version)

            elif self.scheme == VersionScheme.ACCEPT:
                # Extract from Accept header
                accept = request.headers.get('Accept', '')
                if 'version=' in accept:
                    return accept.split('version=')[1].split(';')[0]

            return self.default_version

        except Exception as e:
            logger.error(f"Error extracting version: {str(e)}")
            return self.default_version

class VersionMiddleware(BaseHTTPMiddleware):
    """Middleware for API versioning"""
    
    def __init__(
        self,
        app: FastAPI,
        version_manager: VersionManager,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.version_manager = version_manager
        self.exclude_paths = exclude_paths or {
            '/health',
            '/metrics',
            '/docs',
            '/redoc',
            '/openapi.json'
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        try:
            # Extract version
            version = self.version_manager.extract_version(request)
            api_version = self.version_manager.get_version(version)

            if not api_version:
                return Response(
                    content=f"Unsupported API version: {version}",
                    status_code=400
                )

            # Add version to request state
            request.state.api_version = version

            # Handle deprecated versions
            if api_version.deprecated:
                headers = {
                    'Warning': f'299 - "Deprecated API Version {version}"'
                }
                if api_version.deprecated_message:
                    headers['X-API-Deprecated-Message'] = api_version.deprecated_message
                if api_version.sunset_date:
                    headers['Sunset'] = api_version.sunset_date

                response = await call_next(request)
                response.headers.update(headers)
                return response

            return await call_next(request)

        except Exception as e:
            logger.error(f"Version middleware error: {str(e)}")
            return Response(
                content="Internal server error",
                status_code=500
            )

# Global version manager instance
version_manager = VersionManager(
    default_version=settings.API_DEFAULT_VERSION,
    scheme=VersionScheme[settings.API_VERSION_SCHEME.upper()]
)

# Register supported versions
version_manager.register_version("1.0")
version_manager.register_version(
    "0.9",
    deprecated=True,
    deprecated_message="Please upgrade to v1.0",
    sunset_date="2024-12-31"
)

# Example usage:
"""
version_manager = VersionManager(scheme=VersionScheme.HEADER)

# Register endpoint versions
version_manager.register_endpoint(
    "/api/users",
    "1.0.0",
    min_version="1.0.0",
    max_version="2.0.0"
)

# Add middleware to FastAPI app
app.add_middleware(
    VersioningMiddleware,
    version_manager=version_manager,
    strict=True
)

# In your route handlers:
@app.get("/api/users")
async def get_users(request: Request):
    version = request.state.api_version
    if version.major == 1:
        return {"message": "Version 1 response"}
    else:
        return {"message": "Version 2 response"}
""" 