from typing import Dict, Optional, Any, List, Union, Callable
from dataclasses import dataclass, field
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

@dataclass
class TransformationRule:
    field: str
    transformer: Callable
    description: str
    apply_to_response: bool = False

class RequestTransformer:
    def __init__(self):
        self._rules: Dict[str, List[TransformationRule]] = {}

    def add_rule(
        self,
        path: str,
        method: str,
        rule: TransformationRule
    ) -> None:
        key = f"{method.upper()} {path}"
        if key not in self._rules:
            self._rules[key] = []
        self._rules[key].append(rule)

    def transform_value(
        self,
        value: Any,
        transformer: Callable
    ) -> Any:
        try:
            if isinstance(value, list):
                return [self.transform_value(v, transformer) for v in value]
            elif isinstance(value, dict):
                return {k: self.transform_value(v, transformer) for k, v in value.items()}
            return transformer(value)
        except Exception as e:
            logger.error(f"Transformation error: {str(e)}")
            return value

    def transform_data(
        self,
        request: Request,
        data: Optional[Dict[str, Any]] = None,
        is_response: bool = False
    ) -> Optional[Dict[str, Any]]:
        if not data:
            return None

        key = f"{request.method.upper()} {request.url.path}"
        if key not in self._rules:
            return data

        transformed = data.copy()
        for rule in self._rules[key]:
            if rule.apply_to_response != is_response:
                continue

            if rule.field in transformed:
                transformed[rule.field] = self.transform_value(
                    transformed[rule.field],
                    rule.transformer
                )

        return transformed

class TransformationMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        transformer: Optional[RequestTransformer] = None,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.transformer = transformer or RequestTransformer()
        self.exclude_paths = exclude_paths or {
            '/health',
            '/metrics',
            '/docs',
            '/redoc',
            '/openapi.json'
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        try:
            # Transform request body
            if request.method in ['POST', 'PUT', 'PATCH']:
                body_bytes = await request.body()
                if body_bytes:
                    import json
                    try:
                        body = json.loads(body_bytes)
                        transformed_body = self.transformer.transform_data(
                            request,
                            body,
                            is_response=False
                        )
                        
                        if transformed_body:
                            async def get_body():
                                return json.dumps(transformed_body).encode()
                            request._body = get_body
                    except json.JSONDecodeError:
                        pass

            # Get response
            response = await call_next(request)

            # Transform response body
            if response.headers.get('content-type') == 'application/json':
                body = response.body.decode()
                try:
                    data = json.loads(body)
                    transformed_data = self.transformer.transform_data(
                        request,
                        data,
                        is_response=True
                    )
                    
                    if transformed_data:
                        return Response(
                            content=json.dumps(transformed_data),
                            status_code=response.status_code,
                            headers=dict(response.headers)
                        )
                except json.JSONDecodeError:
                    pass

            return response
            
        except Exception as e:
            logger.error(f"Error in request/response transformation: {str(e)}")
            return await call_next(request)

# Example usage:
"""
transformer = RequestTransformer()

# Add transformation rules
def transform_date(value: str) -> str:
    from datetime import datetime
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return dt.strftime('%Y-%m-%d %H:%M:%S')

transformer.add_rule(
    "/api/events",
    "GET",
    TransformationRule(
        field="timestamp",
        transformer=transform_date,
        description="Convert ISO dates to readable format",
        apply_to_response=True
    )
)

# Add middleware to FastAPI app
app.add_middleware(
    TransformationMiddleware,
    transformer=transformer
)
""" 