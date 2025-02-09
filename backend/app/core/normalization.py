from typing import Dict, Optional, Any, List, Union, Callable
from dataclasses import dataclass, field
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

@dataclass
class NormalizationRule:
    field: str
    normalizer: Callable
    description: str
    apply_to_response: bool = False

class RequestNormalizer:
    def __init__(self):
        self._rules: Dict[str, List[NormalizationRule]] = {}
        self._default_normalizers = {
            'trim_whitespace': lambda x: x.strip() if isinstance(x, str) else x,
            'lowercase': lambda x: x.lower() if isinstance(x, str) else x,
            'uppercase': lambda x: x.upper() if isinstance(x, str) else x,
            'remove_spaces': lambda x: x.replace(' ', '') if isinstance(x, str) else x,
            'normalize_phone': lambda x: ''.join(c for c in str(x) if c.isdigit()) if x else x,
            'normalize_email': lambda x: x.lower().strip() if isinstance(x, str) else x
        }

    def add_rule(
        self,
        path: str,
        method: str,
        rule: NormalizationRule
    ) -> None:
        key = f"{method.upper()} {path}"
        if key not in self._rules:
            self._rules[key] = []
        self._rules[key].append(rule)

    def add_default_normalizer(
        self,
        name: str,
        normalizer: Callable
    ) -> None:
        self._default_normalizers[name] = normalizer

    def normalize_value(
        self,
        value: Any,
        normalizer: Callable
    ) -> Any:
        try:
            if isinstance(value, list):
                return [self.normalize_value(v, normalizer) for v in value]
            elif isinstance(value, dict):
                return {k: self.normalize_value(v, normalizer) for k, v in value.items()}
            return normalizer(value)
        except Exception as e:
            logger.error(f"Normalization error: {str(e)}")
            return value

    def normalize_data(
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

        normalized = data.copy()
        for rule in self._rules[key]:
            if rule.apply_to_response != is_response:
                continue

            if rule.field in normalized:
                normalized[rule.field] = self.normalize_value(
                    normalized[rule.field],
                    rule.normalizer
                )

        return normalized

class NormalizationMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        normalizer: Optional[RequestNormalizer] = None,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.normalizer = normalizer or RequestNormalizer()
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
            # Normalize request body
            if request.method in ['POST', 'PUT', 'PATCH']:
                body_bytes = await request.body()
                if body_bytes:
                    import json
                    try:
                        body = json.loads(body_bytes)
                        normalized_body = self.normalizer.normalize_data(
                            request,
                            body,
                            is_response=False
                        )
                        
                        if normalized_body:
                            async def get_body():
                                return json.dumps(normalized_body).encode()
                            request._body = get_body
                    except json.JSONDecodeError:
                        pass

            # Get response
            response = await call_next(request)

            # Normalize response body
            if response.headers.get('content-type') == 'application/json':
                body = response.body.decode()
                try:
                    data = json.loads(body)
                    normalized_data = self.normalizer.normalize_data(
                        request,
                        data,
                        is_response=True
                    )
                    
                    if normalized_data:
                        return Response(
                            content=json.dumps(normalized_data),
                            status_code=response.status_code,
                            headers=dict(response.headers)
                        )
                except json.JSONDecodeError:
                    pass

            return response
            
        except Exception as e:
            logger.error(f"Error in request/response normalization: {str(e)}")
            return await call_next(request)

# Example usage:
"""
normalizer = RequestNormalizer()

# Add custom normalizer
def normalize_address(value: str) -> str:
    import re
    # Remove extra spaces and standardize common abbreviations
    value = re.sub(r'\s+', ' ', value.strip())
    replacements = {
        'street': 'st',
        'avenue': 'ave',
        'road': 'rd',
        'boulevard': 'blvd',
        'apartment': 'apt'
    }
    for old, new in replacements.items():
        value = re.sub(rf'\b{old}\b', new, value, flags=re.IGNORECASE)
    return value.lower()

normalizer.add_default_normalizer('address', normalize_address)

# Add normalization rules
normalizer.add_rule(
    "/api/users",
    "POST",
    NormalizationRule(
        field="email",
        normalizer=normalizer._default_normalizers['normalize_email'],
        description="Normalize email to lowercase and trim"
    )
)

normalizer.add_rule(
    "/api/users",
    "POST",
    NormalizationRule(
        field="phone",
        normalizer=normalizer._default_normalizers['normalize_phone'],
        description="Remove non-digit characters from phone number"
    )
)

# Add middleware to FastAPI app
app.add_middleware(
    NormalizationMiddleware,
    normalizer=normalizer
)
""" 