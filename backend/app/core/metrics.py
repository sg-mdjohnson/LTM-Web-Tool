from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import time
import psutil
import asyncio
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import (
    Counter, Gauge, Histogram, Summary,
    generate_latest, CONTENT_TYPE_LATEST
)
from app.core.logging import logger

@dataclass
class MetricDefinition:
    """Definition for a metric to be tracked"""
    name: str
    description: str
    metric_type: str
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None  # For histograms
    quantiles: Optional[List[float]] = None  # For summaries

class MetricsManager:
    def __init__(self):
        self._metrics: Dict[str, Any] = {}
        self._start_time = time.time()
        
        # Initialize default metrics
        self._setup_default_metrics()

    def _setup_default_metrics(self) -> None:
        """Setup default application metrics"""
        self.add_metric(MetricDefinition(
            name='app_uptime_seconds',
            description='Application uptime in seconds',
            metric_type='gauge'
        ))

        self.add_metric(MetricDefinition(
            name='app_requests_total',
            description='Total number of HTTP requests',
            metric_type='counter',
            labels=['method', 'path', 'status']
        ))

        self.add_metric(MetricDefinition(
            name='app_request_duration_seconds',
            description='HTTP request duration in seconds',
            metric_type='histogram',
            labels=['method', 'path'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
        ))

        self.add_metric(MetricDefinition(
            name='app_request_size_bytes',
            description='HTTP request size in bytes',
            metric_type='summary',
            labels=['method', 'path'],
            quantiles=[0.5, 0.9, 0.99]
        ))

        self.add_metric(MetricDefinition(
            name='app_response_size_bytes',
            description='HTTP response size in bytes',
            metric_type='summary',
            labels=['method', 'path'],
            quantiles=[0.5, 0.9, 0.99]
        ))

        # System metrics
        self.add_metric(MetricDefinition(
            name='system_cpu_usage_percent',
            description='System CPU usage percentage',
            metric_type='gauge'
        ))

        self.add_metric(MetricDefinition(
            name='system_memory_usage_bytes',
            description='System memory usage in bytes',
            metric_type='gauge',
            labels=['type']
        ))

        self.add_metric(MetricDefinition(
            name='system_disk_usage_bytes',
            description='System disk usage in bytes',
            metric_type='gauge',
            labels=['type']
        ))

    def add_metric(self, definition: MetricDefinition) -> None:
        """Add a new metric based on its definition"""
        try:
            if definition.name in self._metrics:
                logger.warning(f"Metric {definition.name} already exists")
                return

            if definition.metric_type == 'counter':
                metric = Counter(
                    definition.name,
                    definition.description,
                    definition.labels
                )
            elif definition.metric_type == 'gauge':
                metric = Gauge(
                    definition.name,
                    definition.description,
                    definition.labels
                )
            elif definition.metric_type == 'histogram':
                metric = Histogram(
                    definition.name,
                    definition.description,
                    definition.labels,
                    buckets=definition.buckets
                )
            elif definition.metric_type == 'summary':
                metric = Summary(
                    definition.name,
                    definition.description,
                    definition.labels,
                    quantiles=definition.quantiles
                )
            else:
                raise ValueError(f"Unknown metric type: {definition.metric_type}")

            self._metrics[definition.name] = metric
            
        except Exception as e:
            logger.error(f"Error adding metric {definition.name}: {str(e)}")

    def get_metric(self, name: str) -> Optional[Any]:
        """Get a metric by name"""
        return self._metrics.get(name)

    async def update_system_metrics(self) -> None:
        """Update system-related metrics"""
        try:
            # CPU usage
            cpu_metric = self.get_metric('system_cpu_usage_percent')
            if cpu_metric:
                cpu_metric.set(psutil.cpu_percent())

            # Memory usage
            memory = psutil.virtual_memory()
            memory_metric = self.get_metric('system_memory_usage_bytes')
            if memory_metric:
                memory_metric.labels(type='total').set(memory.total)
                memory_metric.labels(type='available').set(memory.available)
                memory_metric.labels(type='used').set(memory.used)

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_metric = self.get_metric('system_disk_usage_bytes')
            if disk_metric:
                disk_metric.labels(type='total').set(disk.total)
                disk_metric.labels(type='free').set(disk.free)
                disk_metric.labels(type='used').set(disk.used)

            # Update uptime
            uptime_metric = self.get_metric('app_uptime_seconds')
            if uptime_metric:
                uptime_metric.set(time.time() - self._start_time)

        except Exception as e:
            logger.error(f"Error updating system metrics: {str(e)}")

class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        metrics_manager: Optional[MetricsManager] = None,
        metrics_path: str = '/metrics',
        update_system_metrics: bool = True,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.metrics_manager = metrics_manager or MetricsManager()
        self.metrics_path = metrics_path
        self.update_system_metrics = update_system_metrics
        self.exclude_paths = exclude_paths or {
            '/health',
            '/metrics',
            '/docs',
            '/redoc',
            '/openapi.json'
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        # Handle metrics endpoint
        if request.url.path == self.metrics_path:
            if self.update_system_metrics:
                await self.metrics_manager.update_system_metrics()
            return Response(
                content=generate_latest(),
                media_type=CONTENT_TYPE_LATEST
            )

        # Skip metrics for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        try:
            # Record request metrics
            start_time = time.time()
            method = request.method
            path = request.url.path

            # Track request size
            request_size = len(await request.body())
            request_size_metric = self.metrics_manager.get_metric('app_request_size_bytes')
            if request_size_metric:
                request_size_metric.labels(method=method, path=path).observe(request_size)

            # Get response
            response = await call_next(request)

            # Record response metrics
            duration = time.time() - start_time
            status = response.status_code

            # Update request counter
            requests_total = self.metrics_manager.get_metric('app_requests_total')
            if requests_total:
                requests_total.labels(
                    method=method,
                    path=path,
                    status=status
                ).inc()

            # Update duration histogram
            duration_metric = self.metrics_manager.get_metric('app_request_duration_seconds')
            if duration_metric:
                duration_metric.labels(method=method, path=path).observe(duration)

            # Track response size
            response_size = len(response.body)
            response_size_metric = self.metrics_manager.get_metric('app_response_size_bytes')
            if response_size_metric:
                response_size_metric.labels(method=method, path=path).observe(response_size)

            return response

        except Exception as e:
            logger.error(f"Error in metrics middleware: {str(e)}")
            return await call_next(request) 