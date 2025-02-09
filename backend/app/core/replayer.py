from typing import Dict, Optional, Any, List, Union
import time
import json
import aiohttp
from dataclasses import dataclass, field
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

@dataclass
class ReplayRequest:
    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, str] = field(default_factory=dict)
    body: Optional[Union[Dict[str, Any], str]] = None

@dataclass
class ReplayResponse:
    status_code: int
    headers: Dict[str, str]
    body: Optional[str]
    duration: float

class RequestReplayer:
    def __init__(
        self,
        target_base_url: str,
        timeout: float = 30.0,
        verify_ssl: bool = True
    ):
        self.target_base_url = target_base_url.rstrip('/')
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def replay_request(
        self,
        request: ReplayRequest
    ) -> ReplayResponse:
        if not self._session:
            raise RuntimeError("Replayer not initialized. Use async with.")

        url = f"{self.target_base_url}{request.url}"
        start_time = time.time()

        try:
            async with self._session.request(
                method=request.method,
                url=url,
                headers=request.headers,
                params=request.query_params,
                json=request.body if isinstance(request.body, dict) else None,
                data=request.body if isinstance(request.body, str) else None,
                ssl=self.verify_ssl
            ) as response:
                duration = time.time() - start_time
                body = await response.text()

                return ReplayResponse(
                    status_code=response.status,
                    headers=dict(response.headers),
                    body=body,
                    duration=duration
                )

        except Exception as e:
            logger.error(
                f"Error replaying request: {str(e)}",
                extra={
                    'url': url,
                    'method': request.method,
                    'error': str(e)
                }
            )
            raise

class ReplayMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        target_url: str,
        enable_replay: bool = False,
        record_differences: bool = True
    ):
        super().__init__(app)
        self.target_url = target_url
        self.enable_replay = enable_replay
        self.record_differences = record_differences
        self.differences: List[Dict[str, Any]] = []

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.enable_replay:
            return await call_next(request)

        # Get original response
        original_response = await call_next(request)
        
        if self.record_differences:
            try:
                # Prepare replay request
                replay_request = ReplayRequest(
                    method=request.method,
                    url=request.url.path,
                    headers=dict(request.headers),
                    query_params=dict(request.query_params)
                )

                if request.method in ['POST', 'PUT', 'PATCH']:
                    body = await request.body()
                    try:
                        replay_request.body = json.loads(body)
                    except json.JSONDecodeError:
                        replay_request.body = body.decode()

                # Replay request
                async with RequestReplayer(self.target_url) as replayer:
                    replay_response = await replayer.replay_request(replay_request)

                # Compare responses
                if (
                    original_response.status_code != replay_response.status_code or
                    original_response.body.decode() != replay_response.body
                ):
                    self.differences.append({
                        'timestamp': time.time(),
                        'path': request.url.path,
                        'method': request.method,
                        'original': {
                            'status_code': original_response.status_code,
                            'body': original_response.body.decode()
                        },
                        'replay': {
                            'status_code': replay_response.status_code,
                            'body': replay_response.body
                        }
                    })

            except Exception as e:
                logger.error(f"Error in replay comparison: {str(e)}")

        return original_response

    def get_differences(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        return self.differences[-limit:] 