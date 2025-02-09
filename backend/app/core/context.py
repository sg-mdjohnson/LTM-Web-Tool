from typing import Dict, Any, Optional
from contextvars import ContextVar
from uuid import uuid4
from datetime import datetime
import asyncio
from app.core.logging import logger
from dataclasses import dataclass, field
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time

request_context: ContextVar[Dict[str, Any]] = ContextVar('request_context', default={})

@dataclass
class RequestContext:
    request_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: Optional[str] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    _current: ContextVar = ContextVar('request_context')

    def __post_init__(self):
        self._current.set(self)

    @classmethod
    def get_current(cls) -> 'RequestContext':
        try:
            return cls._current.get()
        except LookupError:
            return cls()

    def add_tag(self, key: str, value: Any) -> None:
        self.tags[key] = value

    def get_tag(self, key: str, default: Any = None) -> Any:
        return self.tags.get(key, default)

    def get_all_tags(self) -> Dict[str, Any]:
        return self.tags.copy()

    def get_duration(self) -> float:
        return (datetime.utcnow() - self.get_tag('start_time')).total_seconds()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(
                f"Error in request context: {str(exc_val)}",
                extra={'request_id': self.request_id}
            )

class ContextMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or {
            '/health',
            '/metrics'
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Create new request context
        context = RequestContext()
        
        # Add basic request information
        context.add_tag('start_time', time.time())
        context.add_tag('method', request.method)
        context.add_tag('path', request.url.path)
        context.add_tag('client_ip', request.client.host)
        context.add_tag('user_agent', request.headers.get('user-agent'))

        # Add correlation ID if present
        correlation_id = request.headers.get('X-Correlation-ID')
        if correlation_id:
            context.add_tag('correlation_id', correlation_id)

        # Store request ID in request state for access in route handlers
        request.state.request_id = context.request_id

        try:
            response = await call_next(request)
            
            # Add response information
            context.add_tag('status_code', response.status_code)
            context.add_tag('end_time', time.time())
            
            # Add context information to response headers
            response.headers['X-Request-ID'] = context.request_id
            
            return response
            
        except Exception as e:
            # Add error information
            context.add_tag('error', str(e))
            context.add_tag('error_type', e.__class__.__name__)
            raise
            
        finally:
            # Log request completion
            duration = time.time() - context.get_tag('start_time')
            logger.info(
                f"Request completed: {request.method} {request.url.path}",
                extra={
                    'request_id': context.request_id,
                    'duration': duration,
                    'tags': context.get_all_tags()
                }
            ) 