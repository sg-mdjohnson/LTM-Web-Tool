from typing import Dict, Optional, Any, List, Union, Callable
from dataclasses import dataclass, field
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

@dataclass
class AggregationRule:
    field: str
    aggregator: Callable
    description: str
    group_by: Optional[List[str]] = None
    apply_to_response: bool = True

class RequestAggregator:
    def __init__(self):
        self._rules: Dict[str, List[AggregationRule]] = {}
        self._default_aggregators = {
            'count': len,
            'sum': sum,
            'avg': lambda x: sum(x) / len(x) if x else 0,
            'min': min,
            'max': max
        }

    def add_rule(
        self,
        path: str,
        method: str,
        rule: AggregationRule
    ) -> None:
        key = f"{method.upper()} {path}"
        if key not in self._rules:
            self._rules[key] = []
        self._rules[key].append(rule)

    def add_default_aggregator(
        self,
        name: str,
        aggregator: Callable
    ) -> None:
        self._default_aggregators[name] = aggregator

    def _group_data(
        self,
        data: List[Dict[str, Any]],
        group_by: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        groups: Dict[str, List[Dict[str, Any]]] = {}
        
        for item in data:
            # Create group key from specified fields
            key_parts = [str(item.get(field, '')) for field in group_by]
            group_key = '|'.join(key_parts)
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(item)
            
        return groups

    def aggregate_data(
        self,
        request: Request,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        is_response: bool = False
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        key = f"{request.method.upper()} {request.url.path}"
        if key not in self._rules:
            return data

        # Convert single dict to list for uniform processing
        data_list = [data] if isinstance(data, dict) else data
        if not data_list:
            return data

        result = []
        for rule in self._rules[key]:
            if rule.apply_to_response != is_response:
                continue

            try:
                if rule.group_by:
                    # Group data first
                    groups = self._group_data(data_list, rule.group_by)
                    
                    # Apply aggregation to each group
                    for group_key, group_data in groups.items():
                        group_values = [
                            item[rule.field]
                            for item in group_data
                            if rule.field in item
                        ]
                        
                        if group_values:
                            group_result = {
                                'group': dict(zip(rule.group_by, group_key.split('|'))),
                                rule.field: rule.aggregator(group_values)
                            }
                            result.append(group_result)
                else:
                    # Apply aggregation to all data
                    values = [
                        item[rule.field]
                        for item in data_list
                        if rule.field in item
                    ]
                    
                    if values:
                        result.append({
                            rule.field: rule.aggregator(values)
                        })

            except Exception as e:
                logger.error(
                    f"Aggregation error: {str(e)}",
                    extra={
                        'field': rule.field,
                        'path': request.url.path
                    }
                )

        return result if len(result) > 1 else result[0] if result else data

class AggregationMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        aggregator: Optional[RequestAggregator] = None,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.aggregator = aggregator or RequestAggregator()
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

            # Aggregate response data if it's JSON
            if response.headers.get('content-type') == 'application/json':
                body = response.body.decode()
                try:
                    import json
                    data = json.loads(body)
                    aggregated_data = self.aggregator.aggregate_data(
                        request,
                        data,
                        is_response=True
                    )
                    
                    if aggregated_data != data:
                        return Response(
                            content=json.dumps(aggregated_data),
                            status_code=response.status_code,
                            headers=dict(response.headers)
                        )
                except json.JSONDecodeError:
                    pass

            return response
            
        except Exception as e:
            logger.error(f"Error in response aggregation: {str(e)}")
            return await call_next(request)

# Example usage:
"""
aggregator = RequestAggregator()

# Add custom aggregator
def weighted_avg(values: List[Dict[str, float]]) -> float:
    total = sum(v['value'] * v['weight'] for v in values)
    weights = sum(v['weight'] for v in values)
    return total / weights if weights else 0

aggregator.add_default_aggregator('weighted_avg', weighted_avg)

# Add aggregation rules
aggregator.add_rule(
    "/api/sales",
    "GET",
    AggregationRule(
        field="amount",
        aggregator=aggregator._default_aggregators['sum'],
        description="Total sales amount",
        group_by=['category', 'region']
    )
)

aggregator.add_rule(
    "/api/products",
    "GET",
    AggregationRule(
        field="rating",
        aggregator=aggregator._default_aggregators['avg'],
        description="Average product rating",
        group_by=['category']
    )
)

# Add middleware to FastAPI app
app.add_middleware(
    AggregationMiddleware,
    aggregator=aggregator
)
""" 