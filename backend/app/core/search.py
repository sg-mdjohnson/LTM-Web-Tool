from typing import Dict, Optional, Any, List, Union, Callable
from dataclasses import dataclass, field
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

@dataclass
class SearchField:
    name: str
    weight: float = 1.0
    preprocess: Optional[Callable[[Any], str]] = None
    description: str = ""

class SearchEngine:
    def __init__(self):
        self._fields: Dict[str, SearchField] = {}
        self._default_preprocessors = {
            'lowercase': lambda x: str(x).lower(),
            'strip': lambda x: str(x).strip(),
            'normalize': lambda x: ''.join(c.lower() for c in str(x) if c.isalnum())
        }

    def add_field(self, field: SearchField) -> None:
        self._fields[field.name] = field

    def add_preprocessor(
        self,
        name: str,
        preprocessor: Callable
    ) -> None:
        self._default_preprocessors[name] = preprocessor

    def _preprocess_value(
        self,
        value: Any,
        field: SearchField
    ) -> str:
        if field.preprocess:
            try:
                return field.preprocess(value)
            except Exception as e:
                logger.error(f"Error preprocessing search value: {str(e)}")
                return str(value)
        return str(value)

    def _calculate_score(
        self,
        item: Dict[str, Any],
        query: str,
        preprocessed_query: str
    ) -> float:
        score = 0.0
        
        for field_name, field in self._fields.items():
            if field_name in item:
                value = item[field_name]
                preprocessed_value = self._preprocess_value(value, field)
                
                # Exact match has highest weight
                if query.lower() == str(value).lower():
                    score += field.weight * 2.0
                # Preprocessed match has medium weight
                elif preprocessed_query in preprocessed_value:
                    score += field.weight * 1.0
                # Partial match has lowest weight
                elif query.lower() in str(value).lower():
                    score += field.weight * 0.5
                    
        return score

    def search(
        self,
        data: List[Dict[str, Any]],
        query: str,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        if not query or not data:
            return data

        try:
            # Preprocess query
            preprocessed_query = self._default_preprocessors['normalize'](query)
            
            # Calculate scores for each item
            scored_items = []
            for item in data:
                score = self._calculate_score(item, query, preprocessed_query)
                if score > min_score:
                    scored_items.append((score, item))
            
            # Sort by score descending
            scored_items.sort(key=lambda x: x[0], reverse=True)
            
            # Return items without scores
            return [item for score, item in scored_items]
            
        except Exception as e:
            logger.error(f"Error performing search: {str(e)}")
            return data

class SearchMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        search_engine: Optional[SearchEngine] = None,
        exclude_paths: Optional[set] = None,
        query_param: str = 'q',
        min_score: float = 0.1
    ):
        super().__init__(app)
        self.search_engine = search_engine or SearchEngine()
        self.exclude_paths = exclude_paths or {
            '/health',
            '/metrics',
            '/docs',
            '/redoc',
            '/openapi.json'
        }
        self.query_param = query_param
        self.min_score = min_score

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        try:
            # Get search query
            query = request.query_params.get(self.query_param)
            if not query:
                return await call_next(request)

            # Get response
            response = await call_next(request)

            # Search response data if it's JSON
            if response.headers.get('content-type') == 'application/json':
                body = response.body.decode()
                try:
                    import json
                    data = json.loads(body)
                    
                    # Handle both list and dict responses
                    if isinstance(data, list):
                        searched_data = self.search_engine.search(
                            data,
                            query,
                            self.min_score
                        )
                    elif isinstance(data, dict) and 'items' in data:
                        data['items'] = self.search_engine.search(
                            data['items'],
                            query,
                            self.min_score
                        )
                        searched_data = data
                    else:
                        searched_data = data

                    return Response(
                        content=json.dumps(searched_data),
                        status_code=response.status_code,
                        headers=dict(response.headers)
                    )
                except json.JSONDecodeError:
                    pass

            return response
            
        except Exception as e:
            logger.error(f"Error in search middleware: {str(e)}")
            return await call_next(request)

# Example usage:
"""
search_engine = SearchEngine()

# Add custom preprocessor
def preprocess_name(value: str) -> str:
    # Remove titles and normalize
    value = value.lower()
    for title in ['mr.', 'mrs.', 'ms.', 'dr.']:
        value = value.replace(title, '')
    return ''.join(c for c in value if c.isalnum())

search_engine.add_preprocessor('name', preprocess_name)

# Add searchable fields
search_engine.add_field(
    SearchField(
        name='name',
        weight=2.0,
        preprocess=preprocess_name,
        description='User full name'
    )
)

search_engine.add_field(
    SearchField(
        name='email',
        weight=1.5,
        preprocess=search_engine._default_preprocessors['lowercase'],
        description='User email'
    )
)

search_engine.add_field(
    SearchField(
        name='bio',
        weight=1.0,
        preprocess=search_engine._default_preprocessors['normalize'],
        description='User biography'
    )
)

# Add middleware to FastAPI app
app.add_middleware(
    SearchMiddleware,
    search_engine=search_engine,
    query_param='search',
    min_score=0.2
)

# Example queries:
# /api/users?search=john
# /api/users?search=developer
""" 