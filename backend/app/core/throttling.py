from typing import Dict, Tuple, Optional, Any, List, Union, Callable
import time
from threading import Lock
import asyncio
from dataclasses import dataclass, field
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.core.errors import ThrottlingError

@dataclass
class ThrottleConfig:
    rate: int  # Number of requests
    period: int  # Time period in seconds
    burst: Optional[int] = None  # Burst limit
    key_func: Optional[Callable[[Request], str]] = None
    wait: bool = False  # Whether to wait or reject when limit exceeded

class TokenBucket:
    def __init__(self, rate: int, period: int, burst: Optional[int] = None):
        self.rate = rate
        self.period = period
        self.burst = burst or rate
        self.tokens = self.burst
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, wait: bool = False) -> bool:
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(
                self.burst,
                self.tokens + elapsed * (self.rate / self.period)
            )
            self.last_update = now

            if self.tokens >= 1:
                self.tokens -= 1
                return True

            if wait:
                wait_time = (1 - self.tokens) * (self.period / self.rate)
                await asyncio.sleep(wait_time)
                self.tokens = 0
                return True

            return False

class RequestThrottler:
    def __init__(self):
        self._configs: Dict[str, ThrottleConfig] = {}
        self._buckets: Dict[str, Dict[str, TokenBucket]] = {}

    def add_config(
        self,
        path: str,
        method: str,
        config: ThrottleConfig
    ) -> None:
        key = f"{method.upper()} {path}"
        self._configs[key] = config
        self._buckets[key] = {}

    def _get_bucket_key(self, request: Request, config: ThrottleConfig) -> str:
        if config.key_func:
            return config.key_func(request)
        return request.client.host or 'default'

    async def check_rate_limit(
        self,
        request: Request
    ) -> bool:
        key = f"{request.method.upper()} {request.url.path}"
        if key not in self._configs:
            return True

        config = self._configs[key]
        bucket_key = self._get_bucket_key(request, config)
        
        if bucket_key not in self._buckets[key]:
            self._buckets[key][bucket_key] = TokenBucket(
                config.rate,
                config.period,
                config.burst
            )

        return await self._buckets[key][bucket_key].acquire(config.wait)

class ThrottlingMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        throttler: Optional[RequestThrottler] = None,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.throttler = throttler or RequestThrottler()
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
            # Check rate limit
            allowed = await self.throttler.check_rate_limit(request)
            if not allowed:
                return Response(
                    content="Rate limit exceeded",
                    status_code=429,
                    headers={'Retry-After': '60'}
                )

            return await call_next(request)
            
        except Exception as e:
            logger.error(f"Error in request throttling: {str(e)}")
            return await call_next(request)

# Example usage:
"""
throttler = RequestThrottler()

# Add throttle configuration for API endpoints
throttler.add_config(
    "/api/users",
    "GET",
    ThrottleConfig(
        rate=10,  # 10 requests
        period=60,  # per minute
        burst=15,  # allow burst of 15
        wait=True  # wait instead of reject
    )
)

# Add throttle with custom key function
def get_user_key(request: Request) -> str:
    # Rate limit by user ID from token
    auth_token = request.headers.get('Authorization')
    if auth_token:
        # Extract user ID from token
        return f"user:{auth_token}"
    return request.client.host or 'default'

throttler.add_config(
    "/api/posts",
    "POST",
    ThrottleConfig(
        rate=5,  # 5 requests
        period=60,  # per minute
        key_func=get_user_key,
        wait=False  # reject when limit exceeded
    )
)

# Add middleware to FastAPI app
app.add_middleware(
    ThrottlingMiddleware,
    throttler=throttler
)
""" 