from typing import Dict, Any, Optional
import time
from datetime import datetime
from threading import Lock
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

class APIMetricsCollector:
    def __init__(self):
        self._metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: defaultdict(int))
        self._timings: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(list))
        self._lock = Lock()
        self._last_cleanup = time.time()
        self._cleanup_interval = 3600  # 1 hour

    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float,
        client_ip: str
    ) -> None:
        with self._lock:
            key = f"{method}:{path}"
            
            # Update request counts
            self._metrics[key]['total_requests'] += 1
            self._metrics[key][f'status_{status_code}'] += 1
            
            # Update timing statistics
            self._timings[key]['durations'].append(duration)
            if len(self._timings[key]['durations']) > 1000:
                self._timings[key]['durations'] = self._timings[key]['durations'][-1000:]
            
            # Record unique clients
            if 'unique_clients' not in self._metrics[key]:
                self._metrics[key]['unique_clients'] = set()
            self._metrics[key]['unique_clients'].add(client_ip)

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            self._cleanup_old_metrics()
            
            metrics = {}
            for key, data in self._metrics.items():
                metrics[key] = {
                    'total_requests': data['total_requests'],
                    'status_codes': {
                        k: v for k, v in data.items()
                        if k.startswith('status_')
                    },
                    'unique_clients': len(data['unique_clients']),
                    'timing_stats': self._calculate_timing_stats(key)
                }
            return metrics

    def _calculate_timing_stats(self, key: str) -> Dict[str, float]:
        durations = self._timings[key]['durations']
        if not durations:
            return {}

        return {
            'min': min(durations),
            'max': max(durations),
            'avg': sum(durations) / len(durations),
            'p95': sorted(durations)[int(len(durations) * 0.95)]
        }

    def _cleanup_old_metrics(self) -> None:
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        try:
            # Reset metrics older than cleanup interval
            self._metrics.clear()
            self._timings.clear()
            self._last_cleanup = now
        except Exception as e:
            logger.error(f"Error cleaning up metrics: {str(e)}")

class APIMetricsMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        metrics_collector: APIMetricsCollector
    ):
        super().__init__(app)
        self.metrics_collector = metrics_collector

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        self.metrics_collector.record_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=duration,
            client_ip=request.client.host
        )

        return response 