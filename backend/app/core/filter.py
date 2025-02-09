from typing import Any, Dict, List, Optional, Union, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import re
from app.core.logging import logger

class RequestFilter:
    def __init__(self):
        self.filters: Dict[str, Callable] = {}

    def register_filter(
        self,
        name: str,
        filter_func: Callable[[Any], bool]
    ) -> None:
        """Register a new filter function"""
        self.filters[name] = filter_func

    def apply_filter(
        self,
        data: Any,
        filter_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Apply a registered filter to the data"""
        if filter_name not in self.filters:
            raise ValueError(f"Filter not found: {filter_name}")

        try:
            filter_func = self.filters[filter_name]
            return filter_func(data, context) if context else filter_func(data)
        except Exception as e:
            logger.error(
                f"Error applying filter {filter_name}: {str(e)}",
                extra={'context': context}
            )
            raise

    def filter_dict(
        self,
        data: Dict[str, Any],
        filter_map: Dict[str, str]
    ) -> Dict[str, Any]:
        """Apply filters to dictionary fields based on a mapping"""
        filtered = {}
        for key, value in data.items():
            if key in filter_map:
                if self.apply_filter(value, filter_map[key]):
                    filtered[key] = value
            else:
                filtered[key] = value
        return filtered

class RequestFilterMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        request_filter: RequestFilter,
        route_filters: Dict[str, Dict[str, str]]
    ):
        super().__init__(app)
        self.request_filter = request_filter
        self.route_filters = route_filters

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        filters = self.route_filters.get(path)

        if not filters:
            return await call_next(request)

        try:
            # Filter request body if needed
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.json()
                filtered_body = self.request_filter.filter_dict(body, filters)
                # Modify request body
                setattr(request, "_json", filtered_body)

            # Filter query parameters if needed
            query_params = dict(request.query_params)
            if query_params and filters:
                filtered_params = self.request_filter.filter_dict(
                    query_params,
                    filters
                )
                # Update query parameters
                request.scope["query_string"] = (
                    "&".join(f"{k}={v}" for k, v in filtered_params.items())
                ).encode()

        except Exception as e:
            logger.error(f"Error filtering request: {str(e)}")
            # Continue with original request if filtering fails
            pass

        return await call_next(request)

# Example filters
def not_empty(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)

def is_numeric(value: Any) -> bool:
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        return value.replace('.', '').isdigit()
    return False

def is_email(value: str) -> bool:
    if not isinstance(value, str):
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, value))

def is_url(value: str) -> bool:
    if not isinstance(value, str):
        return False
    pattern = r'^https?:\/\/([\w\d\-]+\.)+\w{2,}(\/.*)?$'
    return bool(re.match(pattern, value))

def in_range(value: Union[int, float], min_val: float, max_val: float) -> bool:
    try:
        num_value = float(value)
        return min_val <= num_value <= max_val
    except (ValueError, TypeError):
        return False

# Register common filters
request_filter = RequestFilter()
request_filter.register_filter('not_empty', not_empty)
request_filter.register_filter('numeric', is_numeric)
request_filter.register_filter('email', is_email)
request_filter.register_filter('url', is_url)
request_filter.register_filter('range', in_range) 