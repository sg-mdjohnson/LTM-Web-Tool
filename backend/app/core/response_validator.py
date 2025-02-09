from typing import Any, Dict, Optional, Type, Union
from fastapi import Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from app.core.logging import logger
from app.core.errors import ValidationError as AppValidationError

class ResponseValidator:
    @staticmethod
    def validate_response_data(
        data: Any,
        model: Type[BaseModel]
    ) -> BaseModel:
        try:
            return model.parse_obj(data)
        except ValidationError as e:
            logger.error(
                f"Response validation failed: {str(e)}",
                extra={'validation_errors': e.errors()}
            )
            raise AppValidationError(
                message="Response validation failed",
                details=e.errors()
            )
        except Exception as e:
            logger.error(f"Error validating response data: {str(e)}")
            raise AppValidationError(message="Invalid response data")

    @staticmethod
    def validate_response(
        response: Response,
        expected_status: Optional[int] = None,
        expected_headers: Optional[Dict[str, str]] = None,
        model: Optional[Type[BaseModel]] = None
    ) -> None:
        errors = []

        # Validate status code
        if expected_status and response.status_code != expected_status:
            errors.append(
                f"Unexpected status code: {response.status_code} "
                f"(expected {expected_status})"
            )

        # Validate headers
        if expected_headers:
            for header, expected_value in expected_headers.items():
                actual_value = response.headers.get(header)
                if actual_value != expected_value:
                    errors.append(
                        f"Unexpected value for header {header}: {actual_value} "
                        f"(expected {expected_value})"
                    )

        # Validate response body
        if model and isinstance(response, JSONResponse):
            try:
                ResponseValidator.validate_response_data(
                    response.body,
                    model
                )
            except AppValidationError as e:
                errors.extend(e.details)

        if errors:
            raise AppValidationError(
                message="Response validation failed",
                details=errors
            )

class ResponseValidationMiddleware:
    def __init__(self, app, response_models: Dict[str, Type[BaseModel]]):
        self.app = app
        self.response_models = response_models

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path = scope["path"]
        response_model = self.response_models.get(path)

        if not response_model:
            return await self.app(scope, receive, send)

        async def wrapped_send(message):
            if message["type"] == "http.response.body":
                try:
                    ResponseValidator.validate_response_data(
                        message["body"],
                        response_model
                    )
                except AppValidationError as e:
                    logger.error(
                        f"Response validation failed for {path}: {str(e)}",
                        extra={'validation_errors': e.details}
                    )
                    # In production, you might want to handle this differently
                    raise

            await send(message)

        await self.app(scope, receive, wrapped_send) 