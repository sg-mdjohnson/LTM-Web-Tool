from typing import Dict, Optional, Any, List, Type
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.core.logging import logger

@dataclass
class APIEndpoint:
    path: str
    method: str
    summary: str
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    deprecated: bool = False
    request_model: Optional[Type[BaseModel]] = None
    response_model: Optional[Type[BaseModel]] = None
    responses: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    security: List[Dict[str, List[str]]] = field(default_factory=list)

class DocumentationManager:
    def __init__(self, app: FastAPI):
        self.app = app
        self._endpoints: Dict[str, APIEndpoint] = {}
        self._tags: Dict[str, Dict[str, str]] = {}
        self._security_schemes: Dict[str, Dict[str, Any]] = {}

    def register_endpoint(self, endpoint: APIEndpoint) -> None:
        key = f"{endpoint.method.upper()} {endpoint.path}"
        self._endpoints[key] = endpoint
        logger.info(f"Registered documentation for endpoint: {key}")

    def add_tag(
        self,
        name: str,
        description: str,
        external_docs: Optional[Dict[str, str]] = None
    ) -> None:
        self._tags[name] = {
            'name': name,
            'description': description
        }
        if external_docs:
            self._tags[name]['externalDocs'] = external_docs

    def add_security_scheme(
        self,
        name: str,
        scheme_type: str,
        description: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        self._security_schemes[name] = {
            'type': scheme_type,
            **kwargs
        }
        if description:
            self._security_schemes[name]['description'] = description

    def generate_openapi(self) -> Dict[str, Any]:
        """Generate OpenAPI documentation"""
        if not self.app.openapi_schema:
            openapi_schema = get_openapi(
                title=self.app.title,
                version=self.app.version,
                description=self.app.description,
                routes=self.app.routes
            )

            # Add custom tags
            openapi_schema['tags'] = [
                tag for tag in self._tags.values()
            ]

            # Add security schemes
            if self._security_schemes:
                openapi_schema['components']['securitySchemes'] = self._security_schemes

            # Enhance paths with additional documentation
            for path, path_item in openapi_schema['paths'].items():
                for method, operation in path_item.items():
                    endpoint_key = f"{method.upper()} {path}"
                    if endpoint_key in self._endpoints:
                        endpoint = self._endpoints[endpoint_key]
                        operation.update(self._get_operation_docs(endpoint))

            self.app.openapi_schema = openapi_schema

        return self.app.openapi_schema

    def _get_operation_docs(self, endpoint: APIEndpoint) -> Dict[str, Any]:
        """Generate OpenAPI operation object for endpoint"""
        docs = {
            'summary': endpoint.summary,
            'tags': endpoint.tags
        }

        if endpoint.description:
            docs['description'] = endpoint.description

        if endpoint.deprecated:
            docs['deprecated'] = True

        if endpoint.security:
            docs['security'] = endpoint.security

        if endpoint.responses:
            docs['responses'] = endpoint.responses

        return docs

class APIDocumentation:
    def __init__(self, app: FastAPI):
        self.app = app
        self.doc_manager = DocumentationManager(app)

    def setup(self) -> None:
        """Setup API documentation"""
        # Add common tags
        self.doc_manager.add_tag(
            'auth',
            'Authentication endpoints',
            {
                'description': 'OAuth2 authentication flow',
                'url': 'https://oauth.net/2/'
            }
        )

        # Add security schemes
        self.doc_manager.add_security_scheme(
            'bearer',
            'http',
            scheme='bearer',
            bearerFormat='JWT',
            description='JWT token authentication'
        )

        # Register endpoint documentation
        self.doc_manager.register_endpoint(
            APIEndpoint(
                path="/auth/login",
                method="post",
                summary="User login",
                description="Authenticate user and return JWT token",
                tags=['auth'],
                responses={
                    200: {
                        'description': 'Successful login',
                        'content': {
                            'application/json': {
                                'example': {
                                    'access_token': 'eyJ0...',
                                    'token_type': 'bearer'
                                }
                            }
                        }
                    },
                    401: {
                        'description': 'Invalid credentials'
                    }
                }
            )
        )

        # Generate OpenAPI schema
        self.app.openapi = self.doc_manager.generate_openapi

# Example usage:
"""
app = FastAPI(title="My API", version="1.0.0")
docs = APIDocumentation(app)
docs.setup()
""" 