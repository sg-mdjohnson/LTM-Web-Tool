from typing import Dict, Optional, Any, Union, Callable
import time
import json
import hashlib
from dataclasses import dataclass
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

@dataclass
class CacheConfig:
    ttl: int  # Time to live in seconds
    key_builder: Optional[Callable[[Request], str]] = None
    vary_by_headers: Optional[List[str]] = None
    vary_by_query: Optional[List[str]] = None
    condition: Optional[Callable[[Request], bool]] = None

class CacheBackend:
    """Abstract base class for cache backends"""
    async def get(self, key: str) -> Optional[bytes]:
        raise NotImplementedError()

    async def set(self, key: str, value: bytes, ttl: int) -> None:
        raise NotImplementedError()

    async def delete(self, key: str) -> None:
        raise NotImplementedError()

class InMemoryCache(CacheBackend):
    def __init__(self):
        self._cache: Dict[str, tuple[bytes, float]] = {}

    async def get(self, key: str) -> Optional[bytes]:
        if key in self._cache:
            value, expiry = self._cache[key]
            if expiry > time.time():
                return value
            del self._cache[key]
        return None

    async def set(self, key: str, value: bytes, ttl: int) -> None:
        self._cache[key] = (value, time.time() + ttl)

    async def delete(self, key: str) -> None:
        self._cache.pop(key, None)

class RequestCache:
    def __init__(self, backend: Optional[CacheBackend] = None):
        self._backend = backend or InMemoryCache()
        self._configs: Dict[str, CacheConfig] = {}

    def add_config(
        self,
        path: str,
        method: str,
        config: CacheConfig
    ) -> None:
        key = f"{method.upper()} {path}"
        self._configs[key] = config

    def _build_cache_key(
        self,
        request: Request,
        config: CacheConfig
    ) -> str:
        if config.key_builder:
            return config.key_builder(request)

        # Build key from path and relevant parts
        key_parts = [request.url.path]

        # Add query parameters
        if config.vary_by_query:
            query_params = dict(request.query_params)
            key_parts.extend(
                f"{k}={query_params.get(k, '')}"
                for k in sorted(config.vary_by_query)
            )

        # Add headers
        if config.vary_by_headers:
            headers = dict(request.headers)
            key_parts.extend(
                f"{k}={headers.get(k, '')}"
                for k in sorted(config.vary_by_headers)
            )

        # Hash the key
        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    async def get_cached_response(
        self,
        request: Request
    ) -> Optional[Response]:
        key = f"{request.method.upper()} {request.url.path}"
        if key not in self._configs:
            return None

        config = self._configs[key]
        
        # Check cache condition
        if config.condition and not config.condition(request):
            return None

        cache_key = self._build_cache_key(request, config)
        cached_data = await self._backend.get(cache_key)
        
        if cached_data:
            try:
                data = json.loads(cached_data)
                return Response(
                    content=data['body'],
                    status_code=data['status_code'],
                    headers=data['headers']
                )
            except Exception as e:
                logger.error(f"Error loading cached response: {str(e)}")
                return None

        return None

    async def cache_response(
        self,
        request: Request,
        response: Response
    ) -> None:
        key = f"{request.method.upper()} {request.url.path}"
        if key not in self._configs:
            return

        config = self._configs[key]
        
        # Check cache condition
        if config.condition and not config.condition(request):
            return

        try:
            cache_key = self._build_cache_key(request, config)
            cache_data = {
                'body': response.body.decode(),
                'status_code': response.status_code,
                'headers': dict(response.headers)
            }
            
            await self._backend.set(
                cache_key,
                json.dumps(cache_data).encode(),
                config.ttl
            )
        except Exception as e:
            logger.error(f"Error caching response: {str(e)}")

class CacheMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        cache: Optional[RequestCache] = None,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.cache = cache or RequestCache()
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

        # Only cache GET requests by default
        if request.method != 'GET':
            return await call_next(request)

        try:
            # Check cache first
            cached_response = await self.cache.get_cached_response(request)
            if cached_response:
                return cached_response

            # Get fresh response
            response = await call_next(request)

            # Cache successful JSON responses
            if (
                response.status_code == 200 and
                response.headers.get('content-type') == 'application/json'
            ):
                await self.cache.cache_response(request, response)

            return response
            
        except Exception as e:
            logger.error(f"Error in request caching: {str(e)}")
            return await call_next(request)

# Example usage:
"""
cache = RequestCache()

# Add cache configuration for user list
cache.add_config(
    "/api/users",
    "GET",
    CacheConfig(
        ttl=300,  # Cache for 5 minutes
        vary_by_query=['page', 'limit'],
        vary_by_headers=['Authorization']
    )
)

# Add cache configuration with custom key builder
def build_user_cache_key(request: Request) -> str:
    user_id = request.path_params.get('user_id')
    return f"user:{user_id}"

cache.add_config(
    "/api/users/{user_id}",
    "GET",
    CacheConfig(
        ttl=600,  # Cache for 10 minutes
        key_builder=build_user_cache_key
    )
)

# Add middleware to FastAPI app
app.add_middleware(
    CacheMiddleware,
    cache=cache
)
""" 