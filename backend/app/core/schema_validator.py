from typing import Any, Dict, List, Optional, Type, Union
import json
import jsonschema
from pathlib import Path
from fastapi import Request
from app.core.logging import logger
from app.core.errors import ValidationError as AppValidationError

class SchemaValidator:
    def __init__(self, schema_dir: Path):
        self.schema_dir = schema_dir
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self._load_schemas()

    def _load_schemas(self) -> None:
        try:
            for schema_file in self.schema_dir.glob("*.json"):
                with open(schema_file) as f:
                    schema = json.load(f)
                    if "$id" in schema:
                        self.schemas[schema["$id"]] = schema
                    else:
                        self.schemas[schema_file.stem] = schema
            logger.info(f"Loaded {len(self.schemas)} JSON schemas")
        except Exception as e:
            logger.error(f"Error loading schemas: {str(e)}")
            raise

    def validate(
        self,
        data: Any,
        schema_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        if schema_id not in self.schemas:
            raise AppValidationError(f"Schema not found: {schema_id}")

        try:
            jsonschema.validate(
                instance=data,
                schema=self.schemas[schema_id]
            )
        except jsonschema.exceptions.ValidationError as e:
            logger.warning(
                f"Schema validation failed: {str(e)}",
                extra={
                    'schema_id': schema_id,
                    'validation_path': list(e.path),
                    'context': context
                }
            )
            raise AppValidationError(
                message=f"Schema validation failed: {e.message}",
                details={
                    'path': list(e.path),
                    'schema_path': list(e.schema_path),
                    'validator': e.validator,
                    'validator_value': e.validator_value
                }
            )
        except Exception as e:
            logger.error(f"Error during schema validation: {str(e)}")
            raise AppValidationError(message="Schema validation failed")

    def get_schema(self, schema_id: str) -> Dict[str, Any]:
        if schema_id not in self.schemas:
            raise AppValidationError(f"Schema not found: {schema_id}")
        return self.schemas[schema_id]

class SchemaValidationMiddleware:
    def __init__(
        self,
        app,
        schema_validator: SchemaValidator,
        route_schemas: Dict[str, str]
    ):
        self.app = app
        self.schema_validator = schema_validator
        self.route_schemas = route_schemas

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path = scope["path"]
        schema_id = self.route_schemas.get(path)

        if not schema_id:
            return await self.app(scope, receive, send)

        async def wrapped_receive():
            message = await receive()
            if message["type"] == "http.request":
                try:
                    body = message.get("body", b"").decode()
                    if body:
                        data = json.loads(body)
                        self.schema_validator.validate(
                            data,
                            schema_id,
                            context={'path': path}
                        )
                except json.JSONDecodeError:
                    raise AppValidationError("Invalid JSON in request body")
            return message

        await self.app(scope, wrapped_receive, send) 