from typing import Dict, Optional, Any, List, Callable
import time
import asyncio
import json
from dataclasses import dataclass, field
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.testclient import TestClient
from app.core.logging import logger

@dataclass
class TestCase:
    name: str
    method: str
    path: str
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, str] = field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    expected_status: int = 200
    expected_headers: Optional[Dict[str, str]] = None
    expected_body: Optional[Dict[str, Any]] = None
    setup: Optional[Callable] = None
    cleanup: Optional[Callable] = None

@dataclass
class TestResult:
    test_case: TestCase
    passed: bool
    status_code: int
    response_headers: Dict[str, str]
    response_body: Any
    duration: float
    error: Optional[str] = None

class APITester:
    def __init__(self, app: FastAPI):
        self.app = app
        self.client = TestClient(app)
        self.test_cases: List[TestCase] = []
        self.results: List[TestResult] = []

    def add_test_case(self, test_case: TestCase) -> None:
        self.test_cases.append(test_case)

    def run_tests(self) -> List[TestResult]:
        self.results.clear()
        
        for test_case in self.test_cases:
            result = self._run_test(test_case)
            self.results.append(result)
            
            if not result.passed:
                logger.error(
                    f"Test failed: {test_case.name}",
                    extra={
                        'test_case': vars(test_case),
                        'result': vars(result)
                    }
                )

        return self.results

    def _run_test(self, test_case: TestCase) -> TestResult:
        try:
            # Run setup if provided
            if test_case.setup:
                test_case.setup()

            start_time = time.time()
            
            # Make request
            response = self.client.request(
                method=test_case.method,
                url=test_case.path,
                headers=test_case.headers,
                params=test_case.query_params,
                json=test_case.body
            )
            
            duration = time.time() - start_time

            # Verify response
            passed = True
            error = None

            if response.status_code != test_case.expected_status:
                passed = False
                error = f"Expected status {test_case.expected_status}, got {response.status_code}"

            if test_case.expected_headers:
                for header, value in test_case.expected_headers.items():
                    if response.headers.get(header) != value:
                        passed = False
                        error = f"Header mismatch: {header}"
                        break

            if test_case.expected_body:
                try:
                    response_body = response.json()
                    if response_body != test_case.expected_body:
                        passed = False
                        error = "Body mismatch"
                except json.JSONDecodeError:
                    passed = False
                    error = "Invalid JSON response"

            return TestResult(
                test_case=test_case,
                passed=passed,
                status_code=response.status_code,
                response_headers=dict(response.headers),
                response_body=response.text,
                duration=duration,
                error=error
            )

        except Exception as e:
            return TestResult(
                test_case=test_case,
                passed=False,
                status_code=0,
                response_headers={},
                response_body=None,
                duration=0,
                error=str(e)
            )
            
        finally:
            # Run cleanup if provided
            if test_case.cleanup:
                test_case.cleanup()

    def get_summary(self) -> Dict[str, Any]:
        if not self.results:
            return {}

        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        total_duration = sum(r.duration for r in self.results)

        return {
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'success_rate': (passed / total) * 100 if total > 0 else 0,
            'total_duration': total_duration,
            'avg_duration': total_duration / total if total > 0 else 0,
            'failed_tests': [
                {
                    'name': r.test_case.name,
                    'error': r.error
                }
                for r in self.results if not r.passed
            ]
        }

class TestingMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        record_requests: bool = False,
        max_records: int = 100
    ):
        super().__init__(app)
        self.record_requests = record_requests
        self.max_records = max_records
        self.recorded_requests: List[Dict[str, Any]] = []

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.record_requests:
            return await call_next(request)

        # Record request details
        request_data = {
            'timestamp': time.time(),
            'method': request.method,
            'path': str(request.url.path),
            'query_params': dict(request.query_params),
            'headers': dict(request.headers)
        }

        if request.method in ['POST', 'PUT', 'PATCH']:
            body = await request.body()
            try:
                request_data['body'] = json.loads(body)
            except json.JSONDecodeError:
                request_data['body'] = body.decode()

        response = await call_next(request)

        # Record response details
        request_data.update({
            'status_code': response.status_code,
            'response_headers': dict(response.headers)
        })

        self.recorded_requests.append(request_data)
        
        # Keep only the last max_records
        if len(self.recorded_requests) > self.max_records:
            self.recorded_requests.pop(0)

        return response 