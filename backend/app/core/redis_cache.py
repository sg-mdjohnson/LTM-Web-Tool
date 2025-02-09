from typing import Dict, Optional, Any, Union
import json
import aioredis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger
from app.core.caching import CacheBackend

class RedisCache(CacheBackend):
    def __init__(
        self,
        redis_url: str,
        prefix: str = 'cache:',
        serializer: Optional[callable] = None,
        deserializer: Optional[callable] = None
    ):
        self.redis_url = redis_url
        self.prefix = prefix
        self.serializer = serializer or json.dumps
        self.deserializer = deserializer or json.loads
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        if not self._redis:
            self._redis = await aioredis.from_url(self.redis_url)

    async def disconnect(self) -> None:
        if self._redis:
            await self._redis.close()
            self._redis = None

    def _get_key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Optional[bytes]:
        try:
            await self.connect()
            value = await self._redis.get(self._get_key(key))
            if value:
                return value
        except Exception as e:
            logger.error(f"Redis get error: {str(e)}")
        return None

    async def set(
        self,
        key: str,
        value: bytes,
        ttl: int
    ) -> None:
        try:
            await self.connect()
            await self._redis.setex(
                self._get_key(key),
                ttl,
                value
            )
        except Exception as e:
            logger.error(f"Redis set error: {str(e)}")

    async def delete(self, key: str) -> None:
        try:
            await self.connect()
            await self._redis.delete(self._get_key(key))
        except Exception as e:
            logger.error(f"Redis delete error: {str(e)}")

    async def clear(self, pattern: str = '*') -> None:
        try:
            await self.connect()
            keys = await self._redis.keys(f"{self.prefix}{pattern}")
            if keys:
                await self._redis.delete(*keys)
        except Exception as e:
            logger.error(f"Redis clear error: {str(e)}")

    async def get_many(
        self,
        keys: List[str]
    ) -> Dict[str, Optional[bytes]]:
        try:
            await self.connect()
            pipe = self._redis.pipeline()
            for key in keys:
                pipe.get(self._get_key(key))
            values = await pipe.execute()
            return dict(zip(keys, values))
        except Exception as e:
            logger.error(f"Redis get_many error: {str(e)}")
            return {key: None for key in keys}

    async def set_many(
        self,
        mapping: Dict[str, tuple[bytes, int]]
    ) -> None:
        try:
            await self.connect()
            pipe = self._redis.pipeline()
            for key, (value, ttl) in mapping.items():
                pipe.setex(self._get_key(key), ttl, value)
            await pipe.execute()
        except Exception as e:
            logger.error(f"Redis set_many error: {str(e)}")

class RedisCacheMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        redis_url: str,
        prefix: str = 'cache:',
        ttl: int = 300,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.cache = RedisCache(redis_url, prefix)
        self.ttl = ttl
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

        # Only cache GET requests
        if request.method != 'GET':
            return await call_next(request)

        try:
            # Generate cache key
            cache_key = f"{request.method}:{request.url.path}:{request.query_params}"
            
            # Try to get from cache
            cached_response = await self.cache.get(cache_key)
            if cached_response:
                data = json.loads(cached_response)
                return Response(
                    content=data['body'],
                    status_code=data['status_code'],
                    headers=data['headers']
                )

            # Get fresh response
            response = await call_next(request)

            # Cache successful JSON responses
            if (
                response.status_code == 200 and
                response.headers.get('content-type') == 'application/json'
            ):
                cache_data = {
                    'body': response.body.decode(),
                    'status_code': response.status_code,
                    'headers': dict(response.headers)
                }
                await self.cache.set(
                    cache_key,
                    json.dumps(cache_data).encode(),
                    self.ttl
                )

            return response
            
        except Exception as e:
            logger.error(f"Error in Redis cache middleware: {str(e)}")
            return await call_next(request)

# Example usage:
"""
# Add middleware to FastAPI app
app.add_middleware(
    RedisCacheMiddleware,
    redis_url='redis://localhost:6379/0',
    prefix='myapp:cache:',
    ttl=300  # Cache for 5 minutes
)
""" 