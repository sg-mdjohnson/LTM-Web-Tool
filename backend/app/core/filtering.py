from typing import Dict, Optional, Any, List, Union, Callable
from dataclasses import dataclass, field
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

@dataclass
class FilterRule:
    field: str
    filter_func: Callable
    description: str
    apply_to_response: bool = False

class RequestFilter:
    def __init__(self):
        self._rules: Dict[str, List[FilterRule]] = {}
        self._default_filters = {
            'remove_empty': lambda x: x if x else None,
            'remove_whitespace': lambda x: x.strip() if isinstance(x, str) else x,
            'remove_special_chars': lambda x: ''.join(c for c in str(x) if c.isalnum()) if x else x
        }

    def add_rule(
        self,
        path: str,
        method: str,
        rule: FilterRule
    ) -> None:
        key = f"{method.upper()} {path}"
        if key not in self._rules:
            self._rules[key] = []
        self._rules[key].append(rule)

    def add_default_filter(
        self,
        name: str,
        filter_func: Callable
    ) -> None:
        self._default_filters[name] = filter_func

    def filter_value(
        self,
        value: Any,
        filter_func: Callable
    ) -> Any:
        try:
            if isinstance(value, list):
                return [v for v in (self.filter_value(v, filter_func) for v in value) if v is not None]
            elif isinstance(value, dict):
                return {k: v for k, v in ((k, self.filter_value(v, filter_func)) for k, v in value.items()) if v is not None}
            return filter_func(value)
        except Exception as e:
            logger.error(f"Filtering error: {str(e)}")
            return value

    def filter_data(
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

        filtered = data.copy()
        for rule in self._rules[key]:
            if rule.apply_to_response != is_response:
                continue

            if rule.field in filtered:
                filtered[rule.field] = self.filter_value(
                    filtered[rule.field],
                    rule.filter_func
                )

        # Remove None values
        filtered = {k: v for k, v in filtered.items() if v is not None}
        return filtered

class FilterMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        filter_: Optional[RequestFilter] = None,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.filter = filter_ or RequestFilter()
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
            # Filter request body
            if request.method in ['POST', 'PUT', 'PATCH']:
                body_bytes = await request.body()
                if body_bytes:
                    import json
                    try:
                        body = json.loads(body_bytes)
                        filtered_body = self.filter.filter_data(
                            request,
                            body,
                            is_response=False
                        )
                        
                        if filtered_body:
                            async def get_body():
                                return json.dumps(filtered_body).encode()
                            request._body = get_body
                    except json.JSONDecodeError:
                        pass

            # Get response
            response = await call_next(request)

            # Filter response body
            if response.headers.get('content-type') == 'application/json':
                body = response.body.decode()
                try:
                    data = json.loads(body)
                    filtered_data = self.filter.filter_data(
                        request,
                        data,
                        is_response=True
                    )
                    
                    if filtered_data:
                        return Response(
                            content=json.dumps(filtered_data),
                            status_code=response.status_code,
                            headers=dict(response.headers)
                        )
                except json.JSONDecodeError:
                    pass

            return response
            
        except Exception as e:
            logger.error(f"Error in request/response filtering: {str(e)}")
            return await call_next(request)

# Example usage:
"""
filter_ = RequestFilter()

# Add custom filter
def filter_sensitive_data(value: Any) -> Any:
    if isinstance(value, str):
        # Remove credit card numbers
        import re
        value = re.sub(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '[REDACTED]', value)
        # Remove SSNs
        value = re.sub(r'\b\d{3}[-]?\d{2}[-]?\d{4}\b', '[REDACTED]', value)
    return value

filter_.add_default_filter('sensitive_data', filter_sensitive_data)

# Add filter rules
filter_.add_rule(
    "/api/users",
    "POST",
    FilterRule(
        field="comments",
        filter_func=filter_.default_filters['sensitive_data'],
        description="Remove sensitive data from comments"
    )
)

# Add middleware to FastAPI app
app.add_middleware(
    FilterMiddleware,
    filter_=filter_
)
""" 