from typing import Dict, Tuple, Optional
import time
from threading import Lock
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger
from app.core.errors import RateLimitExceededError

class RateLimiter:
    def __init__(
        self,
        rate_limit: int = 100,
        window_size: int = 60,
        by_ip: bool = True,
        by_endpoint: bool = True
    ):
        self._requests: Dict[str, Tuple[int, float]] = {}
        self._lock = Lock()
        self._rate_limit = rate_limit
        self._window_size = window_size
        self._by_ip = by_ip
        self._by_endpoint = by_endpoint
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes

    def _get_key(self, request: Request) -> str:
        parts = []
        if self._by_ip:
            parts.append(request.client.host)
        if self._by_endpoint:
            parts.append(f"{request.method}:{request.url.path}")
        return ":".join(parts)

    def check_rate_limit(self, request: Request) -> None:
        key = self._get_key(request)
        now = time.time()
        window_start = now - self._window_size

        with self._lock:
            self._cleanup_old_records()

            if key not in self._requests:
                self._requests[key] = (1, now)
                return

            count, last_request = self._requests[key]

            if last_request < window_start:
                self._requests[key] = (1, now)
                return

            if count >= self._rate_limit:
                wait_time = int(window_start + self._window_size - now)
                logger.warning(
                    f"Rate limit exceeded: {request.method} {request.url.path}",
                    extra={
                        'client_ip': request.client.host,
                        'rate_limit': self._rate_limit,
                        'window_size': self._window_size,
                        'wait_time': wait_time
                    }
                )
                raise RateLimitExceededError(
                    f"Rate limit exceeded. Please wait {wait_time} seconds."
                )

            self._requests[key] = (count + 1, now)

    def _cleanup_old_records(self) -> None:
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        try:
            window_start = now - self._window_size
            self._requests = {
                key: (count, timestamp)
                for key, (count, timestamp) in self._requests.items()
                if timestamp >= window_start
            }
            self._last_cleanup = now
        except Exception as e:
            logger.error(f"Error cleaning up rate limit records: {str(e)}")

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        rate_limiter: Optional[RateLimiter] = None,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
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
            self.rate_limiter.check_rate_limit(request)
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers['X-RateLimit-Limit'] = str(
                self.rate_limiter._rate_limit
            )
            response.headers['X-RateLimit-Window'] = str(
                self.rate_limiter._window_size
            )
            
            return response
            
        except RateLimitExceededError as e:
            return Response(
                content=str(e),
                status_code=429,
                headers={
                    'Retry-After': str(
                        int(time.time() + self.rate_limiter._window_size)
                    )
                }
            ) 