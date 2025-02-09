from typing import Dict, Optional, Any, List, Union, Callable
from dataclasses import dataclass, field
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

@dataclass
class EnrichmentRule:
    field: str
    enricher: Callable
    description: str
    apply_to_response: bool = True
    required_fields: List[str] = field(default_factory=list)

class RequestEnricher:
    def __init__(self):
        self._rules: Dict[str, List[EnrichmentRule]] = {}
        self._default_enrichers = {
            'timestamp': lambda x: {**x, 'timestamp': time.time()},
            'request_id': lambda x: {**x, 'request_id': str(uuid.uuid4())},
            'user_agent': lambda x, request: {**x, 'user_agent': request.headers.get('user-agent')}
        }

    def add_rule(
        self,
        path: str,
        method: str,
        rule: EnrichmentRule
    ) -> None:
        key = f"{method.upper()} {path}"
        if key not in self._rules:
            self._rules[key] = []
        self._rules[key].append(rule)

    def add_default_enricher(
        self,
        name: str,
        enricher: Callable
    ) -> None:
        self._default_enrichers[name] = enricher

    def enrich_data(
        self,
        request: Request,
        data: Dict[str, Any],
        is_response: bool = False
    ) -> Dict[str, Any]:
        key = f"{request.method.upper()} {request.url.path}"
        if key not in self._rules:
            return data

        enriched = data.copy()
        for rule in self._rules[key]:
            if rule.apply_to_response != is_response:
                continue

            # Check if required fields are present
            if all(field in enriched for field in rule.required_fields):
                try:
                    enriched[rule.field] = rule.enricher(
                        {k: enriched[k] for k in rule.required_fields},
                        request
                    )
                except Exception as e:
                    logger.error(
                        f"Enrichment error: {str(e)}",
                        extra={
                            'field': rule.field,
                            'path': request.url.path
                        }
                    )

        return enriched

class EnrichmentMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        enricher: Optional[RequestEnricher] = None,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.enricher = enricher or RequestEnricher()
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
            # Enrich request body
            if request.method in ['POST', 'PUT', 'PATCH']:
                body_bytes = await request.body()
                if body_bytes:
                    import json
                    try:
                        body = json.loads(body_bytes)
                        enriched_body = self.enricher.enrich_data(
                            request,
                            body,
                            is_response=False
                        )
                        
                        if enriched_body:
                            async def get_body():
                                return json.dumps(enriched_body).encode()
                            request._body = get_body
                    except json.JSONDecodeError:
                        pass

            # Get response
            response = await call_next(request)

            # Enrich response body
            if response.headers.get('content-type') == 'application/json':
                body = response.body.decode()
                try:
                    data = json.loads(body)
                    enriched_data = self.enricher.enrich_data(
                        request,
                        data,
                        is_response=True
                    )
                    
                    if enriched_data:
                        return Response(
                            content=json.dumps(enriched_data),
                            status_code=response.status_code,
                            headers=dict(response.headers)
                        )
                except json.JSONDecodeError:
                    pass

            return response
            
        except Exception as e:
            logger.error(f"Error in request/response enrichment: {str(e)}")
            return await call_next(request)

# Example usage:
"""
import time
import uuid
from typing import Dict

enricher = RequestEnricher()

# Add custom enricher
def enrich_user_data(fields: Dict[str, Any], request: Request) -> Dict[str, Any]:
    # Get user info from some service
    user_id = fields.get('user_id')
    if user_id:
        return {
            'user_details': {
                'id': user_id,
                'last_login': time.time(),
                'ip_address': request.client.host
            }
        }
    return {}

enricher.add_default_enricher('user_data', enrich_user_data)

# Add enrichment rules
enricher.add_rule(
    "/api/posts",
    "GET",
    EnrichmentRule(
        field="user_details",
        enricher=enricher._default_enrichers['user_data'],
        description="Add user details to post data",
        required_fields=['user_id']
    )
)

# Add middleware to FastAPI app
app.add_middleware(
    EnrichmentMiddleware,
    enricher=enricher
)
""" 