from typing import Any, Dict, List, Optional, Type, Union
from fastapi import Request, HTTPException
from pydantic import BaseModel, ValidationError
from app.core.logging import logger
from app.schemas.responses import ErrorResponse

class RequestValidator:
    @staticmethod
    async def validate_request_body(
        request: Request,
        model: Type[BaseModel]
    ) -> BaseModel:
        try:
            body = await request.json()
            return model(**body)
        except ValidationError as e:
            logger.warning(
                f"Request validation failed: {str(e)}",
                extra={'request_id': getattr(request.state, 'request_id', None)}
            )
            raise HTTPException(
                status_code=422,
                detail=ErrorResponse(
                    message="Validation Error",
                    details=[
                        {
                            'field': error['loc'][-1],
                            'message': error['msg']
                        }
                        for error in e.errors()
                    ]
                ).dict()
            )
        except Exception as e:
            logger.error(f"Error parsing request body: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    message="Invalid request body"
                ).dict()
            )

    @staticmethod
    def validate_query_params(
        params: Dict[str, Any],
        required: List[str] = None,
        optional: Dict[str, Any] = None,
        type_validators: Dict[str, Type] = None
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

        # Check optional parameters
        if optional:
            for param, default in optional.items():
                validated[param] = params.get(param, default)

        # Validate parameter types
        if type_validators:
            for param, validator in type_validators.items():
                if param in validated:
                    try:
                        validated[param] = validator(validated[param])
                    except (ValueError, TypeError):
                        errors.append(
                            f"Invalid type for parameter {param}. "
                            f"Expected {validator.__name__}"
                        )

        if errors:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    message="Invalid query parameters",
                    details=errors
                ).dict()
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
                except (ValueError, TypeError):
                    errors.append(
                        f"Invalid type for path parameter {param}. "
                        f"Expected {validator.__name__}"
                    )

        if errors:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    message="Invalid path parameters",
                    details=errors
                ).dict()
            )

        return validated 