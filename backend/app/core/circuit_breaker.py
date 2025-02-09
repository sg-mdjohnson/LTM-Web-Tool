from typing import Dict, Optional, Callable
import time
from enum import Enum
from threading import Lock
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger
from app.core.errors import CircuitBreakerOpenError

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: int = 60,
        half_open_timeout: int = 30,
        exclude_exceptions: Optional[tuple] = None
    ):
        self._failure_count = 0
        self._last_failure_time = 0
        self._state = CircuitState.CLOSED
        self._lock = Lock()
        self._failure_threshold = failure_threshold
        self._reset_timeout = reset_timeout
        self._half_open_timeout = half_open_timeout
        self._exclude_exceptions = exclude_exceptions or ()

    def _should_allow_request(self) -> bool:
        now = time.time()

        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.OPEN:
            if now - self._last_failure_time >= self._reset_timeout:
                with self._lock:
                    self._state = CircuitState.HALF_OPEN
                    logger.info("Circuit breaker state changed to HALF_OPEN")
                return True
            return False

        if self._state == CircuitState.HALF_OPEN:
            return True

        return False

    def _handle_success(self) -> None:
        if self._state == CircuitState.HALF_OPEN:
            with self._lock:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                logger.info("Circuit breaker state changed to CLOSED")

    def _handle_failure(self, exception: Exception) -> None:
        if isinstance(exception, self._exclude_exceptions):
            return

        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if (
                self._state == CircuitState.CLOSED and 
                self._failure_count >= self._failure_threshold
            ):
                self._state = CircuitState.OPEN
                logger.warning(
                    "Circuit breaker state changed to OPEN",
                    extra={
                        'failure_count': self._failure_count,
                        'last_error': str(exception)
                    }
                )

            elif self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(
                    "Circuit breaker state changed back to OPEN",
                    extra={'error': str(exception)}
                )

    async def call(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        if not self._should_allow_request():
            raise CircuitBreakerOpenError(
                "Circuit breaker is OPEN. Please try again later."
            )

        try:
            result = await func(*args, **kwargs)
            self._handle_success()
            return result
        except Exception as e:
            self._handle_failure(e)
            raise

class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        circuit_breaker: Optional[CircuitBreaker] = None,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
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
            return await self.circuit_breaker.call(call_next, request)
        except CircuitBreakerOpenError as e:
            return Response(
                content=str(e),
                status_code=503,
                headers={'Retry-After': str(self.circuit_breaker._reset_timeout)}
            ) 