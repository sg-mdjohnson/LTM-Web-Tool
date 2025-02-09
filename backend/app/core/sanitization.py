from typing import Dict, Optional, Any, List, Union, Callable
import re
import html
from dataclasses import dataclass, field
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

@dataclass
class SanitizationRule:
    field: str
    sanitizer: Callable
    description: str

class RequestSanitizer:
    def __init__(self):
        self._rules: Dict[str, List[SanitizationRule]] = {}
        self._default_sanitizers = {
            'html': html.escape,
            'strip': str.strip,
            'lower': str.lower,
            'upper': str.upper
        }

    def add_rule(
        self,
        path: str,
        method: str,
        rule: SanitizationRule
    ) -> None:
        key = f"{method.upper()} {path}"
        if key not in self._rules:
            self._rules[key] = []
        self._rules[key].append(rule)

    def add_default_sanitizer(
        self,
        name: str,
        sanitizer: Callable
    ) -> None:
        self._default_sanitizers[name] = sanitizer

    def sanitize_value(
        self,
        value: Any,
        sanitizer: Callable
    ) -> Any:
        if isinstance(value, str):
            return sanitizer(value)
        elif isinstance(value, list):
            return [self.sanitize_value(v, sanitizer) for v in value]
        elif isinstance(value, dict):
            return {k: self.sanitize_value(v, sanitizer) for k, v in value.items()}
        return value

    def sanitize_request(
        self,
        request: Request,
        body: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        if not body:
            return None

        key = f"{request.method.upper()} {request.url.path}"
        if key not in self._rules:
            return body

        sanitized = body.copy()
        for rule in self._rules[key]:
            if rule.field in sanitized:
                try:
                    sanitized[rule.field] = self.sanitize_value(
                        sanitized[rule.field],
                        rule.sanitizer
                    )
                except Exception as e:
                    logger.error(
                        f"Sanitization error: {str(e)}",
                        extra={
                            'field': rule.field,
                            'path': request.url.path
                        }
                    )

        return sanitized

class SanitizationMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        sanitizer: Optional[RequestSanitizer] = None,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.sanitizer = sanitizer or RequestSanitizer()
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
            # Get and sanitize request body
            if request.method in ['POST', 'PUT', 'PATCH']:
                body_bytes = await request.body()
                if body_bytes:
                    import json
                    try:
                        body = json.loads(body_bytes)
                        sanitized_body = self.sanitizer.sanitize_request(request, body)
                        
                        if sanitized_body:
                            # Replace request body with sanitized version
                            async def get_body():
                                return json.dumps(sanitized_body).encode()
                            request._body = get_body
                    except json.JSONDecodeError:
                        pass

            return await call_next(request)
            
        except Exception as e:
            logger.error(f"Error in request sanitization: {str(e)}")
            return await call_next(request)

# Example usage:
"""
sanitizer = RequestSanitizer()

# Add custom sanitizer
def sanitize_phone(value: str) -> str:
    return re.sub(r'[^0-9+]', '', value)

sanitizer.add_default_sanitizer('phone', sanitize_phone)

# Add sanitization rules
sanitizer.add_rule(
    "/api/users",
    "POST",
    SanitizationRule(
        field="username",
        sanitizer=str.strip,
        description="Remove leading/trailing whitespace"
    )
)

sanitizer.add_rule(
    "/api/users",
    "POST",
    SanitizationRule(
        field="email",
        sanitizer=str.lower,
        description="Convert email to lowercase"
    )
)

# Add middleware to FastAPI app
app.add_middleware(
    SanitizationMiddleware,
    sanitizer=sanitizer
)
""" 