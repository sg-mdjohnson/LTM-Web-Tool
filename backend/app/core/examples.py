from typing import Dict, Optional, Any, List, Union
from dataclasses import dataclass, field
from fastapi import FastAPI
from app.core.logging import logger

@dataclass
class APIExample:
    name: str
    summary: str
    description: Optional[str] = None
    value: Optional[Dict[str, Any]] = None
    external_value: Optional[str] = None
    request_headers: Optional[Dict[str, str]] = None
    request_body: Optional[Dict[str, Any]] = None
    response_headers: Optional[Dict[str, str]] = None
    response_body: Optional[Dict[str, Any]] = None

class ExampleManager:
    def __init__(self):
        self._examples: Dict[str, Dict[str, APIExample]] = {}

    def add_example(
        self,
        path: str,
        method: str,
        example: APIExample
    ) -> None:
        key = f"{method.upper()} {path}"
        if key not in self._examples:
            self._examples[key] = {}
        
        self._examples[key][example.name] = example
        logger.info(f"Added example '{example.name}' for {key}")

    def get_examples(
        self,
        path: str,
        method: str
    ) -> Dict[str, APIExample]:
        key = f"{method.upper()} {path}"
        return self._examples.get(key, {})

    def get_example(
        self,
        path: str,
        method: str,
        name: str
    ) -> Optional[APIExample]:
        examples = self.get_examples(path, method)
        return examples.get(name)

    def to_openapi(
        self,
        path: str,
        method: str
    ) -> Dict[str, Dict[str, Any]]:
        examples = self.get_examples(path, method)
        if not examples:
            return {}

        openapi_examples = {}
        for name, example in examples.items():
            example_doc = {
                'summary': example.summary
            }

            if example.description:
                example_doc['description'] = example.description

            if example.value:
                example_doc['value'] = example.value
            elif example.external_value:
                example_doc['externalValue'] = example.external_value

            openapi_examples[name] = example_doc

        return openapi_examples

class ExampleDocumentation:
    def __init__(self, app: FastAPI):
        self.app = app
        self.example_manager = ExampleManager()

    def setup(self) -> None:
        """Setup API examples"""
        # Add example for user creation
        self.example_manager.add_example(
            "/api/users",
            "post",
            APIExample(
                name="create_user",
                summary="Create a new user",
                description="Example of creating a new user account",
                request_headers={
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer <token>'
                },
                request_body={
                    'username': 'john_doe',
                    'email': 'john@example.com',
                    'password': 'secure_password123'
                },
                response_body={
                    'id': 1,
                    'username': 'john_doe',
                    'email': 'john@example.com',
                    'created_at': '2023-01-01T00:00:00Z'
                }
            )
        )

        # Add example for user login
        self.example_manager.add_example(
            "/auth/login",
            "post",
            APIExample(
                name="user_login",
                summary="User login example",
                request_body={
                    'username': 'john_doe',
                    'password': 'secure_password123'
                },
                response_body={
                    'access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                    'token_type': 'bearer'
                }
            )
        )

        # Update OpenAPI schema to include examples
        def custom_openapi():
            if not self.app.openapi_schema:
                self.app.openapi_schema = self.app.openapi()
                
                # Add examples to paths
                for path, path_item in self.app.openapi_schema['paths'].items():
                    for method, operation in path_item.items():
                        examples = self.example_manager.to_openapi(path, method)
                        if examples:
                            if 'requestBody' in operation:
                                operation['requestBody']['content']['application/json']['examples'] = examples
                            if 'responses' in operation:
                                for response in operation['responses'].values():
                                    if 'content' in response:
                                        response['content']['application/json']['examples'] = examples

            return self.app.openapi_schema

        self.app.openapi = custom_openapi

# Example usage:
"""
app = FastAPI()
examples = ExampleDocumentation(app)
examples.setup()
""" 