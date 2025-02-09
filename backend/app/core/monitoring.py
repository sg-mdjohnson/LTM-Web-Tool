from typing import Dict, Optional, Any
import time
from dataclasses import dataclass, field
from threading import Lock
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger
from app.core.metrics import MetricsCollector

@dataclass
class RequestStats:
    total_requests: int = 0
    active_requests: int = 0
    success_count: int = 0
    error_count: int = 0
    total_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = float('-inf')

    def update(self, duration: float, success: bool) -> None:
        self.total_requests += 1
        self.total_duration += duration
        self.min_duration = min(self.min_duration, duration)
        self.max_duration = max(self.max_duration, duration)
        
        if success:
            self.success_count += 1
        else:
            self.error_count += 1

    @property
    def avg_duration(self) -> float:
        return self.total_duration / self.total_requests if self.total_requests > 0 else 0.0

    @property
    def success_rate(self) -> float:
        return self.success_count / self.total_requests if self.total_requests > 0 else 0.0

class RequestMonitor:
    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        self._stats: Dict[str, RequestStats] = {}
        self._lock = Lock()
        self.metrics_collector = metrics_collector

    def start_request(self, path: str) -> None:
        with self._lock:
            if path not in self._stats:
                self._stats[path] = RequestStats()
            self._stats[path].active_requests += 1

    def end_request(
        self,
        path: str,
        duration: float,
        status_code: int
    ) -> None:
        with self._lock:
            if path in self._stats:
                self._stats[path].active_requests -= 1
                self._stats[path].update(
                    duration,
                    200 <= status_code < 400
                )

                if self.metrics_collector:
                    self.metrics_collector.record(
                        'request.duration',
                        duration,
                        tags={'path': path}
                    )
                    self.metrics_collector.record(
                        'request.active',
                        self._stats[path].active_requests,
                        tags={'path': path}
                    )

    def get_stats(self, path: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            if path:
                if path not in self._stats:
                    return {}
                return self._format_stats(path, self._stats[path])
            
            return {
                path: self._format_stats(path, stats)
                for path, stats in self._stats.items()
            }

    def _format_stats(self, path: str, stats: RequestStats) -> Dict[str, Any]:
        return {
            'path': path,
            'total_requests': stats.total_requests,
            'active_requests': stats.active_requests,
            'success_count': stats.success_count,
            'error_count': stats.error_count,
            'success_rate': stats.success_rate,
            'avg_duration': stats.avg_duration,
            'min_duration': stats.min_duration if stats.min_duration != float('inf') else 0,
            'max_duration': stats.max_duration if stats.max_duration != float('-inf') else 0
        }

class MonitoringMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        request_monitor: Optional[RequestMonitor] = None,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.request_monitor = request_monitor or RequestMonitor()
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

        path = request.url.path
        start_time = time.time()
        self.request_monitor.start_request(path)

        try:
            response = await call_next(request)
            return response
            
        finally:
            duration = time.time() - start_time
            status_code = getattr(response, 'status_code', 500)
            
            self.request_monitor.end_request(
                path,
                duration,
                status_code
            )

            if duration > 1.0:  # Log slow requests
                logger.warning(
                    f"Slow request detected: {request.method} {path}",
                    extra={
                        'duration': duration,
                        'status_code': status_code
                    }
                ) 