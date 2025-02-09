from typing import Dict, Optional, Any, List, Callable, Union
import json
import re
from dataclasses import dataclass, field
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

@dataclass
class MockResponse:
    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Union[Dict[str, Any], str]] = None
    delay: float = 0.0

class MockDefinition:
    def __init__(
        self,
        method: str,
        path: str,
        response: MockResponse,
        match_query_params: bool = False,
        match_headers: bool = False,
        match_body: bool = False
    ):
        self.method = method.upper()
        self.path_pattern = re.compile(path)
        self.response = response
        self.match_query_params = match_query_params
        self.match_headers = match_headers
        self.match_body = match_body
        self.call_count = 0

    def matches(
        self,
        request: Request,
        query_params: Dict[str, str],
        headers: Dict[str, str],
        body: Optional[Dict[str, Any]] = None
    ) -> bool:
        if request.method.upper() != self.method:
            return False

        if not self.path_pattern.match(request.url.path):
            return False

        if self.match_query_params:
            request_params = dict(request.query_params)
            if request_params != query_params:
                return False

        if self.match_headers:
            for key, value in headers.items():
                if request.headers.get(key) != value:
                    return False

        if self.match_body and body:
            try:
                request_body = json.loads(request.body())
                if request_body != body:
                    return False
            except (json.JSONDecodeError, ValueError):
                return False

        return True

class MockServer:
    def __init__(self):
        self._mocks: List[MockDefinition] = []

    def add_mock(self, mock: MockDefinition) -> None:
        self._mocks.append(mock)

    def clear_mocks(self) -> None:
        self._mocks.clear()

    def get_mock(self, request: Request) -> Optional[MockDefinition]:
        for mock in self._mocks:
            if mock.matches(request, {}, {}):
                mock.call_count += 1
                return mock
        return None

    def get_call_counts(self) -> Dict[str, int]:
        return {
            f"{mock.method} {mock.path_pattern.pattern}": mock.call_count
            for mock in self._mocks
        }

class MockMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        mock_server: Optional[MockServer] = None,
        enable_mocking: bool = False
    ):
        super().__init__(app)
        self.mock_server = mock_server or MockServer()
        self.enable_mocking = enable_mocking

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.enable_mocking:
            return await call_next(request)

        mock = self.mock_server.get_mock(request)
        if not mock:
            return await call_next(request)

        if mock.response.delay > 0:
            import asyncio
            await asyncio.sleep(mock.response.delay)

        body = mock.response.body
        if isinstance(body, dict):
            body = json.dumps(body)

        return Response(
            content=body,
            status_code=mock.response.status_code,
            headers=mock.response.headers
        )

# Example usage:
"""
# Create mock responses
mock_server = MockServer()

# Add a mock for GET /users
mock_server.add_mock(
    MockDefinition(
        method="GET",
        path="/api/users",
        response=MockResponse(
            status_code=200,
            body={
                "users": [
                    {"id": 1, "name": "Test User"}
                ]
            }
        )
    )
)

# Add a mock with pattern matching
mock_server.add_mock(
    MockDefinition(
        method="GET",
        path=r"/api/users/\d+",
        response=MockResponse(
            status_code=200,
            body={"id": 1, "name": "Test User"}
        )
    )
)

# Add mock with specific headers and query params
mock_server.add_mock(
    MockDefinition(
        method="GET",
        path="/api/protected",
        match_headers=True,
        headers={"Authorization": "Bearer test"},
        response=MockResponse(
            status_code=200,
            body={"message": "Authorized"}
        )
    )
)

# Add the middleware to your FastAPI app
app.add_middleware(
    MockMiddleware,
    mock_server=mock_server,
    enable_mocking=True
)
""" 