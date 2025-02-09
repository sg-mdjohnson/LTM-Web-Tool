from typing import Dict, Optional, Any, List
import time
import json
from dataclasses import dataclass, field
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

@dataclass
class RequestRecord:
    timestamp: float = field(default_factory=time.time)
    request_id: str = ""
    method: str = ""
    path: str = ""
    query_params: Dict[str, str] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    response_status: int = 0
    response_headers: Dict[str, str] = field(default_factory=dict)
    response_body: Optional[str] = None
    duration: float = 0.0
    error: Optional[str] = None

class RequestRecorder:
    def __init__(
        self,
        max_records: int = 1000,
        record_bodies: bool = True,
        exclude_paths: Optional[set] = None
    ):
        self._records: List[RequestRecord] = []
        self._max_records = max_records
        self._record_bodies = record_bodies
        self.exclude_paths = exclude_paths or {
            '/health',
            '/metrics',
            '/docs',
            '/redoc',
            '/openapi.json'
        }

    def add_record(self, record: RequestRecord) -> None:
        self._records.append(record)
        if len(self._records) > self._max_records:
            self._records.pop(0)

    def get_records(
        self,
        method: Optional[str] = None,
        path: Optional[str] = None,
        status_code: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        filtered = self._records

        if method:
            filtered = [r for r in filtered if r.method == method.upper()]
        if path:
            filtered = [r for r in filtered if r.path == path]
        if status_code:
            filtered = [r for r in filtered if r.response_status == status_code]

        return [self._format_record(r) for r in filtered[-limit:]]

    def _format_record(self, record: RequestRecord) -> Dict[str, Any]:
        return {
            'timestamp': record.timestamp,
            'request_id': record.request_id,
            'method': record.method,
            'path': record.path,
            'query_params': record.query_params,
            'headers': record.headers,
            'body': record.body if self._record_bodies else None,
            'response_status': record.response_status,
            'response_headers': record.response_headers,
            'response_body': record.response_body if self._record_bodies else None,
            'duration': record.duration,
            'error': record.error
        }

    def get_statistics(self) -> Dict[str, Any]:
        if not self._records:
            return {}

        total = len(self._records)
        success = sum(1 for r in self._records if 200 <= r.response_status < 400)
        durations = [r.duration for r in self._records]

        return {
            'total_requests': total,
            'success_count': success,
            'error_count': total - success,
            'avg_duration': sum(durations) / total,
            'min_duration': min(durations),
            'max_duration': max(durations),
            'status_codes': {
                status: sum(1 for r in self._records if r.response_status == status)
                for status in set(r.response_status for r in self._records)
            }
        }

class RecorderMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        recorder: Optional[RequestRecorder] = None,
        enable_recording: bool = True
    ):
        super().__init__(app)
        self.recorder = recorder or RequestRecorder()
        self.enable_recording = enable_recording

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.enable_recording or request.url.path in self.recorder.exclude_paths:
            return await call_next(request)

        start_time = time.time()
        record = RequestRecord(
            request_id=getattr(request.state, 'request_id', ''),
            method=request.method,
            path=str(request.url.path),
            query_params=dict(request.query_params),
            headers=dict(request.headers)
        )

        try:
            # Record request body if available
            if request.method in ['POST', 'PUT', 'PATCH']:
                body = await request.body()
                record.body = body.decode()

            response = await call_next(request)

            # Record response details
            record.response_status = response.status_code
            record.response_headers = dict(response.headers)
            
            # Try to record response body
            if hasattr(response, 'body'):
                record.response_body = response.body.decode()

            return response
            
        except Exception as e:
            record.error = str(e)
            raise
            
        finally:
            record.duration = time.time() - start_time
            self.recorder.add_record(record) 