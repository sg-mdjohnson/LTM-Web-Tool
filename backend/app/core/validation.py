from typing import Any, Dict, List, Optional, Type, Union, Callable
from fastapi import Request, HTTPException
from pydantic import BaseModel, ValidationError
from app.core.logging import logger
from app.core.errors import ValidationError as AppValidationError
from dataclasses import dataclass, field
from starlette.middleware.base import BaseHTTPMiddleware

@dataclass
class ValidationRule:
    """Validation rule definition"""
    field: str
    validator: callable
    error_message: str
    stop_on_fail: bool = False

class RequestValidator:
    """Validates request data against defined rules"""
    
    def __init__(self):
        self._rules: Dict[str, List[ValidationRule]] = {}

    def add_rule(
        self,
        path: str,
        field: str,
        validator: callable,
        error_message: str,
        stop_on_fail: bool = False
    ) -> None:
        """Add a validation rule for a path"""
        if path not in self._rules:
            self._rules[path] = []
            
        self._rules[path].append(
            ValidationRule(
                field=field,
                validator=validator,
                error_message=error_message,
                stop_on_fail=stop_on_fail
            )
        )

    async def validate_request(
        self,
        path: str,
        data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Validate request data against rules"""
        errors = []
        
        if path not in self._rules:
            return errors

        for rule in self._rules[path]:
            try:
                field_value = data.get(rule.field)
                if not rule.validator(field_value):
                    errors.append({
                        'field': rule.field,
                        'message': rule.error_message
                    })
                    if rule.stop_on_fail:
                        break
            except Exception as e:
                logger.error(f"Validation error: {str(e)}")
                errors.append({
                    'field': rule.field,
                    'message': f"Validation error: {str(e)}"
                })
                if rule.stop_on_fail:
                    break

        return errors

class ModelValidator:
    """Validates request data against Pydantic models"""
    
    def __init__(self):
        self._models: Dict[str, Type[BaseModel]] = {}

    def register_model(
        self,
        path: str,
        model: Type[BaseModel]
    ) -> None:
        """Register a Pydantic model for a path"""
        self._models[path] = model

    async def validate_model(
        self,
        path: str,
        data: Dict[str, Any]
    ) -> Optional[BaseModel]:
        """Validate data against registered model"""
        if path not in self._models:
            return None

        try:
            return self._models[path](**data)
        except ValidationError as e:
            errors = []
            for error in e.errors():
                errors.append({
                    'field': '.'.join(str(x) for x in error['loc']),
                    'message': error['msg']
                })
            raise AppValidationError(details=errors)

class ValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for request validation"""
    
    def __init__(
        self,
        app,
        request_validator: Optional[RequestValidator] = None,
        model_validator: Optional[ModelValidator] = None,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.request_validator = request_validator or RequestValidator()
        self.model_validator = model_validator or ModelValidator()
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
            # Get request data
            data = {}
            if request.method in ('POST', 'PUT', 'PATCH'):
                data = await request.json()
            elif request.method == 'GET':
                data = dict(request.query_params)

            # Validate against rules
            errors = await self.request_validator.validate_request(
                request.url.path,
                data
            )
            if errors:
                return Response(
                    content={"errors": errors},
                    status_code=400,
                    media_type="application/json"
                )

            # Validate against model
            try:
                validated_data = await self.model_validator.validate_model(
                    request.url.path,
                    data
                )
                if validated_data:
                    request.state.validated_data = validated_data
            except AppValidationError as e:
                return Response(
                    content={"errors": e.details},
                    status_code=400,
                    media_type="application/json"
                )

            return await call_next(request)

        except Exception as e:
            logger.error(f"Validation middleware error: {str(e)}")
            return Response(
                content="Internal server error",
                status_code=500
            )

    @staticmethod
    def validate_query_params(
        params: Dict[str, Any],
        required: List[str] = None,
        optional: Dict[str, Any] = None,
        validators: Dict[str, Type] = None
    ) -> Dict[str, Any]:
        validated = {}
        errors = []

        # Check required parameters
        if required:
            for param in required:
                if param not in params:
                    errors.append(f"Missing required parameter: {param}")
                else:
                    validated[param] = params[param]

        # Check optional parameters with defaults
        if optional:
            for param, default in optional.items():
                validated[param] = params.get(param, default)

        # Apply type validators
        if validators:
            for param, validator in validators.items():
                if param in validated:
                    try:
                        validated[param] = validator(validated[param])
                    except (ValueError, TypeError) as e:
                        errors.append(
                            f"Invalid value for parameter {param}: {str(e)}"
                        )

        if errors:
            raise AppValidationError(
                message="Query parameter validation failed",
                details=errors
            )

        return validated

    @staticmethod
    def validate_path_params(
        params: Dict[str, str],
        validators: Dict[str, Type]
    ) -> Dict[str, Any]:
        validated = {}
        errors = []

        for param, validator in validators.items():
            if param not in params:
                errors.append(f"Missing path parameter: {param}")
            else:
                try:
                    validated[param] = validator(params[param])
                except (ValueError, TypeError) as e:
                    errors.append(
                        f"Invalid value for path parameter {param}: {str(e)}"
                    )

        if errors:
            raise AppValidationError(
                message="Path parameter validation failed",
                details=errors
            )

        return validated

    @staticmethod
    def validate_headers(
        headers: Dict[str, str],
        required: List[str] = None,
        validators: Dict[str, Type] = None
    ) -> Dict[str, Any]:
        validated = {}
        errors = []

        # Check required headers
        if required:
            for header in required:
                if header not in headers:
                    errors.append(f"Missing required header: {header}")
                else:
                    validated[header] = headers[header]

        # Apply type validators
        if validators:
            for header, validator in validators.items():
                if header in validated:
                    try:
                        validated[header] = validator(validated[header])
                    except (ValueError, TypeError) as e:
                        errors.append(
                            f"Invalid value for header {header}: {str(e)}"
                        )

        if errors:
            raise AppValidationError(
                message="Header validation failed",
                details=errors
            )

        return validated 