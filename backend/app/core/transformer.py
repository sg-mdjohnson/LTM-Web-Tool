from typing import Any, Dict, List, Optional, Union, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json
from app.core.logging import logger

class RequestTransformer:
    def __init__(self):
        self.transforms: Dict[str, Callable] = {}

    def register_transform(
        self,
        name: str,
        transform_func: Callable[[Any], Any]
    ) -> None:
        """Register a new transformation function"""
        self.transforms[name] = transform_func

    def apply_transform(
        self,
        data: Any,
        transform_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Apply a registered transformation to the data"""
        if transform_name not in self.transforms:
            raise ValueError(f"Transform not found: {transform_name}")

        try:
            transform_func = self.transforms[transform_name]
            return transform_func(data, context) if context else transform_func(data)
        except Exception as e:
            logger.error(
                f"Error applying transform {transform_name}: {str(e)}",
                extra={'context': context}
            )
            raise

    def transform_dict(
        self,
        data: Dict[str, Any],
        transform_map: Dict[str, str]
    ) -> Dict[str, Any]:
        """Apply transformations to dictionary fields based on a mapping"""
        transformed = {}
        for key, value in data.items():
            if key in transform_map:
                transformed[key] = self.apply_transform(value, transform_map[key])
            else:
                transformed[key] = value
        return transformed

class RequestTransformMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        transformer: RequestTransformer,
        route_transforms: Dict[str, Dict[str, str]]
    ):
        super().__init__(app)
        self.transformer = transformer
        self.route_transforms = route_transforms

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        transforms = self.route_transforms.get(path)

        if not transforms:
            return await call_next(request)

        try:
            # Transform request body if needed
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.json()
                transformed_body = self.transformer.transform_dict(body, transforms)
                # Modify request body
                setattr(request, "_json", transformed_body)

            # Transform query parameters if needed
            query_params = dict(request.query_params)
            if query_params and transforms:
                transformed_params = self.transformer.transform_dict(
                    query_params,
                    transforms
                )
                # Update query parameters
                request.scope["query_string"] = (
                    "&".join(f"{k}={v}" for k, v in transformed_params.items())
                ).encode()

        except Exception as e:
            logger.error(f"Error transforming request: {str(e)}")
            # Continue with original request if transformation fails
            pass

        return await call_next(request)

# Example transformations
def to_uppercase(value: str) -> str:
    return value.upper() if isinstance(value, str) else value

def to_lowercase(value: str) -> str:
    return value.lower() if isinstance(value, str) else value

def strip_whitespace(value: str) -> str:
    return value.strip() if isinstance(value, str) else value

def to_int(value: Any) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0

def to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'y', 'on')
    return bool(value)

def to_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [x.strip() for x in value.split(',') if x.strip()]
    return [value] if value is not None else []

# Register common transformations
transformer = RequestTransformer()
transformer.register_transform('uppercase', to_uppercase)
transformer.register_transform('lowercase', to_lowercase)
transformer.register_transform('strip', strip_whitespace)
transformer.register_transform('int', to_int)
transformer.register_transform('bool', to_bool)
transformer.register_transform('list', to_list) 