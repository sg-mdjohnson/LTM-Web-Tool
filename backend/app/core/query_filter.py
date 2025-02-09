from typing import Dict, Optional, Any, List, Union, Callable
from dataclasses import dataclass, field
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

@dataclass
class FilterOperator:
    name: str
    func: Callable
    description: str

@dataclass
class FilterField:
    name: str
    operators: List[str]
    type_converter: Optional[Callable] = None
    description: str = ""

class QueryFilter:
    def __init__(self):
        self._fields: Dict[str, FilterField] = {}
        self._operators: Dict[str, FilterOperator] = {
            'eq': FilterOperator('eq', lambda x, y: x == y, 'Equal to'),
            'ne': FilterOperator('ne', lambda x, y: x != y, 'Not equal to'),
            'gt': FilterOperator('gt', lambda x, y: x > y, 'Greater than'),
            'lt': FilterOperator('lt', lambda x, y: x < y, 'Less than'),
            'gte': FilterOperator('gte', lambda x, y: x >= y, 'Greater than or equal to'),
            'lte': FilterOperator('lte', lambda x, y: x <= y, 'Less than or equal to'),
            'in': FilterOperator('in', lambda x, y: x in y, 'In list'),
            'nin': FilterOperator('nin', lambda x, y: x not in y, 'Not in list'),
            'contains': FilterOperator('contains', lambda x, y: y in x, 'Contains'),
            'startswith': FilterOperator('startswith', lambda x, y: x.startswith(y), 'Starts with'),
            'endswith': FilterOperator('endswith', lambda x, y: x.endswith(y), 'Ends with')
        }

    def add_field(self, field: FilterField) -> None:
        self._fields[field.name] = field

    def add_operator(self, operator: FilterOperator) -> None:
        self._operators[operator.name] = operator

    def _parse_filter_value(
        self,
        value: str,
        field: FilterField
    ) -> Any:
        if field.type_converter:
            try:
                return field.type_converter(value)
            except (ValueError, TypeError) as e:
                logger.error(f"Error converting filter value: {str(e)}")
                return value
        return value

    def _parse_query_params(
        self,
        params: Dict[str, str]
    ) -> List[tuple[str, str, Any]]:
        filters = []
        
        for key, value in params.items():
            if '__' in key:
                field_name, operator = key.split('__')
                if (
                    field_name in self._fields and
                    operator in self._operators and
                    operator in self._fields[field_name].operators
                ):
                    parsed_value = self._parse_filter_value(
                        value,
                        self._fields[field_name]
                    )
                    filters.append((field_name, operator, parsed_value))
            
        return filters

    def apply_filters(
        self,
        data: List[Dict[str, Any]],
        filters: List[tuple[str, str, Any]]
    ) -> List[Dict[str, Any]]:
        if not filters:
            return data

        filtered_data = data
        for field_name, operator, value in filters:
            try:
                op = self._operators[operator]
                filtered_data = [
                    item for item in filtered_data
                    if field_name in item and op.func(item[field_name], value)
                ]
            except Exception as e:
                logger.error(
                    f"Error applying filter: {str(e)}",
                    extra={
                        'field': field_name,
                        'operator': operator,
                        'value': value
                    }
                )

        return filtered_data

class QueryFilterMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        query_filter: Optional[QueryFilter] = None,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.query_filter = query_filter or QueryFilter()
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
            # Parse query filters
            filters = self.query_filter._parse_query_params(
                dict(request.query_params)
            )

            # Get response
            response = await call_next(request)

            # Apply filters to response if it's JSON
            if filters and response.headers.get('content-type') == 'application/json':
                body = response.body.decode()
                try:
                    import json
                    data = json.loads(body)
                    
                    # Handle both list and dict responses
                    if isinstance(data, list):
                        filtered_data = self.query_filter.apply_filters(data, filters)
                    elif isinstance(data, dict) and 'items' in data:
                        data['items'] = self.query_filter.apply_filters(data['items'], filters)
                        filtered_data = data
                    else:
                        filtered_data = data

                    return Response(
                        content=json.dumps(filtered_data),
                        status_code=response.status_code,
                        headers=dict(response.headers)
                    )
                except json.JSONDecodeError:
                    pass

            return response
            
        except Exception as e:
            logger.error(f"Error in query filtering: {str(e)}")
            return await call_next(request)

# Example usage:
"""
query_filter = QueryFilter()

# Add filterable fields
query_filter.add_field(
    FilterField(
        name='age',
        operators=['eq', 'gt', 'lt', 'gte', 'lte'],
        type_converter=int,
        description='User age'
    )
)

query_filter.add_field(
    FilterField(
        name='name',
        operators=['eq', 'contains', 'startswith', 'endswith'],
        description='User name'
    )
)

query_filter.add_field(
    FilterField(
        name='status',
        operators=['eq', 'in', 'nin'],
        description='User status'
    )
)

# Add middleware to FastAPI app
app.add_middleware(
    QueryFilterMiddleware,
    query_filter=query_filter
)

# Example queries:
# /api/users?age__gte=18&status__in=active,pending
# /api/users?name__contains=john&age__lt=30
""" 