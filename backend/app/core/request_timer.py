from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
from datetime import datetime
from app.core.logging import logger
from app.core.metrics import MetricsCollector

class RequestTimer:
    def __init__(self):
        self.start_time = time.time()
        self.splits: Dict[str, float] = {}

    def split(self, name: str) -> None:
        self.splits[name] = time.time() - self.start_time

    def get_timings(self) -> Dict[str, float]:
        timings = {
            name: duration
            for name, duration in self.splits.items()
        }
        timings['total'] = time.time() - self.start_time
        return timings

class RequestTimingMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        metrics_collector: MetricsCollector,
        slow_request_threshold: float = 1.0
    ):
        super().__init__(app)
        self.metrics_collector = metrics_collector
        self.slow_request_threshold = slow_request_threshold

    async def dispatch(self, request: Request, call_next) -> Response:
        timer = RequestTimer()
        request.state.timer = timer

        try:
            response = await call_next(request)
            return response
            
        finally:
            timings = timer.get_timings()
            total_time = timings['total']

            # Record metrics
            self.metrics_collector.timing(
                'request.duration',
                total_time,
                tags={
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': getattr(response, 'status_code', 500)
                }
            )

            # Log slow requests
            if total_time > self.slow_request_threshold:
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path}",
                    extra={
                        'request_id': getattr(request.state, 'request_id', None),
                        'duration': total_time,
                        'timings': timings
                    }
                ) 