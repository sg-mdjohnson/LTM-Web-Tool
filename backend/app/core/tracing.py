from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
import time
import uuid
import json
from contextvars import ContextVar
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from app.core.logging import logger

# Context variable to store trace information
trace_context: ContextVar[Dict[str, Any]] = ContextVar('trace_context', default={})

@dataclass
class TraceConfig:
    """Configuration for tracing"""
    service_name: str
    sample_rate: float = 1.0
    max_attributes: int = 100
    exclude_paths: set = field(default_factory=lambda: {
        '/health',
        '/metrics',
        '/docs',
        '/redoc',
        '/openapi.json'
    })

class TracingManager:
    def __init__(self, config: TraceConfig):
        self.config = config
        self.tracer_provider = TracerProvider(
            sampler=trace.sampling.TraceIdRatioBased(self.config.sample_rate)
        )
        self.tracer = self.tracer_provider.get_tracer(
            self.config.service_name
        )

    def add_span_processor(self, processor: BatchSpanProcessor) -> None:
        """Add a span processor to the tracer provider"""
        self.tracer_provider.add_span_processor(processor)

    def start_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        parent: Optional[Span] = None
    ) -> Span:
        """Start a new span"""
        try:
            context = trace.get_current_span().get_span_context() if parent else None
            span = self.tracer.start_span(
                name,
                context=context,
                attributes=attributes
            )
            return span
        except Exception as e:
            logger.error(f"Error starting span: {str(e)}")
            return self.tracer.start_span(name)

    def end_span(
        self,
        span: Span,
        status: Optional[Status] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        """End a span with optional status and attributes"""
        try:
            if status:
                span.set_status(status)
            if attributes:
                # Limit number of attributes
                limited_attrs = dict(list(attributes.items())[:self.config.max_attributes])
                span.set_attributes(limited_attrs)
            span.end()
        except Exception as e:
            logger.error(f"Error ending span: {str(e)}")
            span.end()

    def record_exception(
        self,
        span: Span,
        exception: Exception,
        attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record an exception in the span"""
        try:
            span.record_exception(
                exception,
                attributes=attributes
            )
            span.set_status(Status(StatusCode.ERROR))
        except Exception as e:
            logger.error(f"Error recording exception: {str(e)}")

class TracingMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        tracing_manager: TracingManager
    ):
        super().__init__(app)
        self.tracing_manager = tracing_manager

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.tracing_manager.config.exclude_paths:
            return await call_next(request)

        trace_id = str(uuid.uuid4())
        span = None

        try:
            # Start root span for request
            span = self.tracing_manager.start_span(
                name=f"{request.method} {request.url.path}",
                attributes={
                    'http.method': request.method,
                    'http.url': str(request.url),
                    'http.scheme': request.url.scheme,
                    'http.target': request.url.path,
                    'http.host': request.headers.get('host', ''),
                    'http.user_agent': request.headers.get('user-agent', ''),
                    'http.request_id': trace_id
                }
            )

            # Store trace context
            trace_context.set({
                'trace_id': trace_id,
                'span_id': span.get_span_context().span_id,
                'parent_id': span.get_span_context().parent_id
            })

            # Process request body if present
            if request.method in ('POST', 'PUT', 'PATCH'):
                body = await request.body()
                if body:
                    try:
                        json_body = json.loads(body)
                        span.set_attribute('http.request.body.size', len(body))
                        if len(str(json_body)) <= 1000:  # Limit large payloads
                            span.set_attribute('http.request.body', str(json_body))
                    except json.JSONDecodeError:
                        pass

            # Get response
            start_time = time.time()
            response = await call_next(request)
            duration = time.time() - start_time

            # Add response attributes
            span.set_attributes({
                'http.status_code': response.status_code,
                'http.response.duration': duration,
                'http.response.size': len(response.body)
            })

            # Set span status based on response
            if 200 <= response.status_code < 400:
                span.set_status(Status(StatusCode.OK))
            else:
                span.set_status(Status(StatusCode.ERROR))

            return response

        except Exception as e:
            if span:
                self.tracing_manager.record_exception(span, e)
            logger.error(f"Error in tracing middleware: {str(e)}")
            return await call_next(request)

        finally:
            if span:
                self.tracing_manager.end_span(span)
            trace_context.set({})  # Clear trace context 