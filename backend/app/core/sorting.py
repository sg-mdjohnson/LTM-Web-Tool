from typing import Dict, Optional, Any, List, Union, Callable
from dataclasses import dataclass, field
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

@dataclass
class SortConfig:
    field: str
    direction: str = 'asc'  # 'asc' or 'desc'
    key_func: Optional[Callable[[Any], Any]] = None
    apply_to_response: bool = True

class RequestSorter:
    def __init__(self):
        self._configs: Dict[str, List[SortConfig]] = {}
        self._default_key_funcs = {
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'date': lambda x: x.isoformat() if hasattr(x, 'isoformat') else x
        }

    def add_config(
        self,
        path: str,
        method: str,
        config: SortConfig
    ) -> None:
        key = f"{method.upper()} {path}"
        if key not in self._configs:
            self._configs[key] = []
        self._configs[key].append(config)

    def add_default_key_func(
        self,
        name: str,
        key_func: Callable
    ) -> None:
        self._default_key_funcs[name] = key_func

    def sort_data(
        self,
        request: Request,
        data: Union[List[Dict[str, Any]], Dict[str, Any]],
        is_response: bool = False
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        key = f"{request.method.upper()} {request.url.path}"
        if key not in self._configs:
            return data

        # Handle both list and dict responses
        data_list = data if isinstance(data, list) else data.get('items', [])
        if not data_list:
            return data

        try:
            # Apply each sort config in order
            for config in self._configs[key]:
                if config.apply_to_response != is_response:
                    continue

                reverse = config.direction.lower() == 'desc'
                key_func = config.key_func or (lambda x: x.get(config.field))

                data_list = sorted(
                    data_list,
                    key=key_func,
                    reverse=reverse
                )

            # Return in original format
            if isinstance(data, dict):
                data['items'] = data_list
                return data
            return data_list

        except Exception as e:
            logger.error(
                f"Sorting error: {str(e)}",
                extra={'path': request.url.path}
            )
            return data

class SortingMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        sorter: Optional[RequestSorter] = None,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.sorter = sorter or RequestSorter()
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
            # Get response
            response = await call_next(request)

            # Sort response data if it's JSON
            if response.headers.get('content-type') == 'application/json':
                body = response.body.decode()
                try:
                    import json
                    data = json.loads(body)
                    sorted_data = self.sorter.sort_data(
                        request,
                        data,
                        is_response=True
                    )
                    
                    if sorted_data != data:
                        return Response(
                            content=json.dumps(sorted_data),
                            status_code=response.status_code,
                            headers=dict(response.headers)
                        )
                except json.JSONDecodeError:
                    pass

            return response
            
        except Exception as e:
            logger.error(f"Error in response sorting: {str(e)}")
            return await call_next(request)

# Example usage:
"""
sorter = RequestSorter()

# Add custom key function for nested fields
def get_nested_field(field_path: str) -> Callable:
    def key_func(item: Dict[str, Any]) -> Any:
        value = item
        for key in field_path.split('.'):
            value = value.get(key, {})
        return value
    return key_func

sorter.add_default_key_func('nested', get_nested_field)

# Add sort configurations
sorter.add_config(
    "/api/users",
    "GET",
    SortConfig(
        field="created_at",
        direction="desc"
    )
)

# Sort by nested field
sorter.add_config(
    "/api/orders",
    "GET",
    SortConfig(
        field="customer.name",
        direction="asc",
        key_func=get_nested_field("customer.name")
    )
)

# Add middleware to FastAPI app
app.add_middleware(
    SortingMiddleware,
    sorter=sorter
)
""" 