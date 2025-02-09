from typing import Optional, Set, Union, Callable
import time
import asyncio
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

class RetryStrategy:
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 10.0,
        backoff_factor: float = 2.0,
        retry_on_status_codes: Optional[Set[int]] = None,
        retry_on_exceptions: Optional[tuple] = None
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.retry_on_status_codes = retry_on_status_codes or {
            408, 429, 500, 502, 503, 504
        }
        self.retry_on_exceptions = retry_on_exceptions or (
            ConnectionError,
            TimeoutError
        )

    def should_retry(
        self,
        attempt: int,
        response: Optional[Response] = None,
        exception: Optional[Exception] = None
    ) -> bool:
        if attempt >= self.max_retries:
            return False

        if response and response.status_code in self.retry_on_status_codes:
            return True

        if exception and isinstance(exception, self.retry_on_exceptions):
            return True

        return False

    def get_delay(self, attempt: int) -> float:
        delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
        return min(delay, self.max_delay)

class RetryMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        retry_strategy: Optional[RetryStrategy] = None,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.retry_strategy = retry_strategy or RetryStrategy()
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

        attempt = 1
        while True:
            try:
                response = await call_next(request)
                
                if not self.retry_strategy.should_retry(attempt, response=response):
                    return response

                delay = self.retry_strategy.get_delay(attempt)
                logger.warning(
                    f"Retrying request after {delay}s: {request.method} {request.url.path}",
                    extra={
                        'attempt': attempt,
                        'status_code': response.status_code,
                        'delay': delay
                    }
                )
                
                await asyncio.sleep(delay)
                attempt += 1
                
            except Exception as e:
                if not self.retry_strategy.should_retry(attempt, exception=e):
                    raise

                delay = self.retry_strategy.get_delay(attempt)
                logger.warning(
                    f"Retrying request after {delay}s due to error: {str(e)}",
                    extra={
                        'attempt': attempt,
                        'error': str(e),
                        'delay': delay
                    }
                )
                
                await asyncio.sleep(delay)
                attempt += 1 