from typing import Optional
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger
from app.core.context import RequestContext

class CorrelationMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        header_name: str = "X-Correlation-ID",
        validate_uuid: bool = True
    ):
        super().__init__(app)
        self.header_name = header_name
        self.validate_uuid = validate_uuid

    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = self._get_or_generate_correlation_id(request)
        
        # Store in request context
        context = RequestContext.get_current()
        context.add_tag('correlation_id', correlation_id)
        
        # Add to request state for access in route handlers
        request.state.correlation_id = correlation_id
        
        response = await call_next(request)
        
        # Add to response headers
        response.headers[self.header_name] = correlation_id
        
        return response

    def _get_or_generate_correlation_id(self, request: Request) -> str:
        correlation_id = request.headers.get(self.header_name)
        
        if not correlation_id:
            return str(uuid.uuid4())
            
        if self.validate_uuid:
            try:
                uuid.UUID(correlation_id)
                return correlation_id
            except ValueError:
                logger.warning(f"Invalid correlation ID format: {correlation_id}")
                return str(uuid.uuid4())
                
        return correlation_id

class CorrelationContext:
    def __init__(self, correlation_id: str):
        self.correlation_id = correlation_id
        self._parent_id: Optional[str] = None
        self._span_id = str(uuid.uuid4())

    @property
    def parent_id(self) -> Optional[str]:
        return self._parent_id

    @property
    def span_id(self) -> str:
        return self._span_id

    def create_child(self) -> 'CorrelationContext':
        child = CorrelationContext(self.correlation_id)
        child._parent_id = self.span_id
        return child

    def to_dict(self) -> dict:
        return {
            'correlation_id': self.correlation_id,
            'parent_id': self.parent_id,
            'span_id': self.span_id
        } 