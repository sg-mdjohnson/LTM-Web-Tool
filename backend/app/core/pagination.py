from typing import Dict, Optional, Any, List, Union, Callable, TypeVar
from dataclasses import dataclass
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

T = TypeVar('T')

@dataclass
class PaginationConfig:
    default_limit: int = 10
    max_limit: int = 100
    page_param: str = 'page'
    limit_param: str = 'limit'
    include_total: bool = True
    key_func: Optional[Callable[[Request], str]] = None

@dataclass
class PaginationInfo:
    page: int
    limit: int
    total: Optional[int]
    has_next: bool
    has_prev: bool

class PaginatedResponse:
    def __init__(
        self,
        items: List[T],
        info: PaginationInfo,
        links: Optional[Dict[str, str]] = None
    ):
        self.items = items
        self.info = info
        self.links = links or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'items': self.items,
            'pagination': {
                'page': self.info.page,
                'limit': self.info.limit,
                'total': self.info.total,
                'has_next': self.info.has_next,
                'has_prev': self.info.has_prev
            },
            'links': self.links
        }

class RequestPaginator:
    def __init__(self):
        self._configs: Dict[str, PaginationConfig] = {}

    def add_config(
        self,
        path: str,
        method: str,
        config: PaginationConfig
    ) -> None:
        key = f"{method.upper()} {path}"
        self._configs[key] = config

    def _get_pagination_params(
        self,
        request: Request,
        config: PaginationConfig
    ) -> tuple[int, int]:
        try:
            page = max(1, int(request.query_params.get(config.page_param, 1)))
            limit = min(
                config.max_limit,
                max(1, int(request.query_params.get(config.limit_param, config.default_limit)))
            )
            return page, limit
        except ValueError:
            return 1, config.default_limit

    def _build_links(
        self,
        request: Request,
        info: PaginationInfo,
        config: PaginationConfig
    ) -> Dict[str, str]:
        base_url = str(request.url)
        links = {}

        # Remove existing pagination params
        for param in [config.page_param, config.limit_param]:
            base_url = base_url.replace(f"{param}={request.query_params.get(param, '')}", "")
        base_url = base_url.rstrip('?&')
        separator = '?' if '?' not in base_url else '&'

        if info.has_prev:
            links['prev'] = f"{base_url}{separator}{config.page_param}={info.page-1}&{config.limit_param}={info.limit}"
            links['first'] = f"{base_url}{separator}{config.page_param}=1&{config.limit_param}={info.limit}"

        if info.has_next:
            links['next'] = f"{base_url}{separator}{config.page_param}={info.page+1}&{config.limit_param}={info.limit}"
            if info.total:
                last_page = (info.total - 1) // info.limit + 1
                links['last'] = f"{base_url}{separator}{config.page_param}={last_page}&{config.limit_param}={info.limit}"

        return links

    def paginate_data(
        self,
        request: Request,
        data: Union[List[T], Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        key = f"{request.method.upper()} {request.url.path}"
        if key not in self._configs:
            return None

        config = self._configs[key]
        page, limit = self._get_pagination_params(request, config)

        try:
            # Handle both list and dict responses
            items = data if isinstance(data, list) else data.get('items', [])
            total = len(items) if config.include_total else None

            # Calculate slice indices
            start = (page - 1) * limit
            end = start + limit

            # Get page items
            page_items = items[start:end]
            
            # Create pagination info
            info = PaginationInfo(
                page=page,
                limit=limit,
                total=total,
                has_next=end < len(items),
                has_prev=page > 1
            )

            # Build response with links
            links = self._build_links(request, info, config)
            response = PaginatedResponse(page_items, info, links)

            return response.to_dict()

        except Exception as e:
            logger.error(
                f"Pagination error: {str(e)}",
                extra={'path': request.url.path}
            )
            return None

class PaginationMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        paginator: Optional[RequestPaginator] = None,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.paginator = paginator or RequestPaginator()
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

            # Paginate response if it's JSON
            if response.headers.get('content-type') == 'application/json':
                body = response.body.decode()
                try:
                    import json
                    data = json.loads(body)
                    paginated_data = self.paginator.paginate_data(request, data)
                    
                    if paginated_data:
                        return Response(
                            content=json.dumps(paginated_data),
                            status_code=response.status_code,
                            headers=dict(response.headers)
                        )
                except json.JSONDecodeError:
                    pass

            return response
            
        except Exception as e:
            logger.error(f"Error in response pagination: {str(e)}")
            return await call_next(request)

# Example usage:
"""
paginator = RequestPaginator()

# Add pagination config for list endpoints
paginator.add_config(
    "/api/users",
    "GET",
    PaginationConfig(
        default_limit=20,
        max_limit=100,
        include_total=True
    )
)

# Add pagination with custom key function
def get_tenant_key(request: Request) -> str:
    return request.headers.get('X-Tenant-ID', 'default')

paginator.add_config(
    "/api/tenant/users",
    "GET",
    PaginationConfig(
        default_limit=10,
        max_limit=50,
        key_func=get_tenant_key
    )
)

# Add middleware to FastAPI app
app.add_middleware(
    PaginationMiddleware,
    paginator=paginator
)
""" 