from typing import Optional
import uuid
from contextvars import ContextVar
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="")

class RequestIDMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        header_name: str = "X-Request-ID",
        validate_uuid: bool = True
    ):
        super().__init__(app)
        self.header_name = header_name
        self.validate_uuid = validate_uuid

    async def dispatch(self, request: Request, call_next):
        request_id = self._get_or_generate_request_id(request)
        request_id_ctx_var.set(request_id)
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers[self.header_name] = request_id
        
        return response

    def _get_or_generate_request_id(self, request: Request) -> str:
        request_id = request.headers.get(self.header_name)
        
        if not request_id:
            return str(uuid.uuid4())
            
        if self.validate_uuid:
            try:
                uuid.UUID(request_id)
                return request_id
            except ValueError:
                logger.warning(f"Invalid request ID format: {request_id}")
                return str(uuid.uuid4())
                
        return request_id

def get_request_id() -> str:
    return request_id_ctx_var.get() 