from typing import Dict, Optional, Any, List
import time
import sys
import traceback
from dataclasses import dataclass, field
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

@dataclass
class DebugInfo:
    timestamp: float = field(default_factory=time.time)
    request_id: str = ""
    method: str = ""
    path: str = ""
    query_params: Dict[str, str] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    duration: Optional[float] = None
    python_version: str = field(default_factory=lambda: sys.version)
    memory_usage: Dict[str, float] = field(default_factory=dict)

class RequestDebugger:
    def __init__(self, max_requests: int = 100):
        self._debug_info: List[DebugInfo] = []
        self._max_requests = max_requests

    def add_debug_info(self, debug_info: DebugInfo) -> None:
        self._debug_info.append(debug_info)
        if len(self._debug_info) > self._max_requests:
            self._debug_info.pop(0)

    def get_debug_info(
        self,
        request_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        if request_id:
            info = next(
                (i for i in self._debug_info if i.request_id == request_id),
                None
            )
            return [self._format_debug_info(info)] if info else []

        return [
            self._format_debug_info(info)
            for info in self._debug_info[-limit:]
        ]

    def _format_debug_info(self, debug_info: DebugInfo) -> Dict[str, Any]:
        return {
            'timestamp': debug_info.timestamp,
            'request_id': debug_info.request_id,
            'method': debug_info.method,
            'path': debug_info.path,
            'query_params': debug_info.query_params,
            'headers': debug_info.headers,
            'body': debug_info.body,
            'error': debug_info.error,
            'traceback': debug_info.traceback,
            'duration': debug_info.duration,
            'python_version': debug_info.python_version,
            'memory_usage': debug_info.memory_usage
        }

class DebugMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        debugger: Optional[RequestDebugger] = None,
        debug_mode: bool = False,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.debugger = debugger or RequestDebugger()
        self.debug_mode = debug_mode
        self.exclude_paths = exclude_paths or {
            '/health',
            '/metrics',
            '/docs',
            '/redoc',
            '/openapi.json'
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.debug_mode or request.url.path in self.exclude_paths:
            return await call_next(request)

        start_time = time.time()
        debug_info = DebugInfo(
            request_id=getattr(request.state, 'request_id', ''),
            method=request.method,
            path=str(request.url.path),
            query_params=dict(request.query_params),
            headers=dict(request.headers)
        )

        try:
            # Capture request body if available
            if request.method in ['POST', 'PUT', 'PATCH']:
                body = await request.body()
                debug_info.body = body.decode()

            response = await call_next(request)
            return response
            
        except Exception as e:
            debug_info.error = str(e)
            debug_info.traceback = traceback.format_exc()
            raise
            
        finally:
            debug_info.duration = time.time() - start_time
            
            # Add memory usage information
            import psutil
            process = psutil.Process()
            debug_info.memory_usage = {
                'rss': process.memory_info().rss / 1024 / 1024,  # MB
                'vms': process.memory_info().vms / 1024 / 1024   # MB
            }
            
            self.debugger.add_debug_info(debug_info)
            
            if debug_info.error:
                logger.error(
                    f"Request error: {debug_info.error}",
                    extra=self.debugger._format_debug_info(debug_info)
                )
            elif debug_info.duration > 1.0:  # Log slow requests
                logger.warning(
                    f"Slow request: {request.method} {request.url.path}",
                    extra=self.debugger._format_debug_info(debug_info)
                ) 