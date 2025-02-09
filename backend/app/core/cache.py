from typing import Any, Dict, Optional, Union
import time
from threading import Lock
from datetime import datetime, timedelta
import json
import aioredis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.logging import logger

class CacheManager:
    """Manages application caching with Redis"""
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = 300,
        prefix: str = "cache:",
        serializer: Optional[callable] = None,
        deserializer: Optional[callable] = None
    ):
        self.redis_url = redis_url or settings.REDIS_URI
        self.default_ttl = default_ttl
        self.prefix = prefix
        self.serializer = serializer or json.dumps
        self.deserializer = deserializer or json.loads
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        """Establish Redis connection"""
        if not self._redis:
            try:
                self._redis = await aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
            except Exception as e:
                logger.error(f"Redis connection error: {str(e)}")
                raise

    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self._redis:
            try:
                await self._redis.close()
                self._redis = None
            except Exception as e:
                logger.error(f"Redis disconnect error: {str(e)}")
                raise

    def _get_key(self, key: str) -> str:
        """Get prefixed cache key"""
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            await self.connect()
            value = await self._redis.get(self._get_key(key))
            if value:
                return self.deserializer(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        try:
            await self.connect()
            serialized = self.serializer(value)
            return await self._redis.set(
                self._get_key(key),
                serialized,
                ex=ttl or self.default_ttl
            )
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            await self.connect()
            return bool(await self._redis.delete(self._get_key(key)))
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            await self.connect()
            return bool(await self._redis.exists(self._get_key(key)))
        except Exception as e:
            logger.error(f"Cache exists error: {str(e)}")
            return False

    async def clear(self, pattern: str = "*") -> bool:
        """Clear cache entries matching pattern"""
        try:
            await self.connect()
            keys = await self._redis.keys(self._get_key(pattern))
            if keys:
                return bool(await self._redis.delete(*keys))
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            return False

    async def increment(
        self,
        key: str,
        amount: int = 1,
        ttl: Optional[int] = None
    ) -> Optional[int]:
        """Increment counter in cache"""
        try:
            await self.connect()
            key = self._get_key(key)
            value = await self._redis.incrby(key, amount)
            if ttl:
                await self._redis.expire(key, ttl)
            return value
        except Exception as e:
            logger.error(f"Cache increment error: {str(e)}")
            return None

class CacheMiddleware(BaseHTTPMiddleware):
    """Middleware for response caching"""
    
    def __init__(
        self,
        app,
        cache_manager: Optional[CacheManager] = None,
        ttl: Optional[int] = None,
        exclude_paths: Optional[set] = None,
        cache_by_query: bool = True,
        cache_by_auth: bool = True
    ):
        super().__init__(app)
        self.cache_manager = cache_manager or CacheManager()
        self.ttl = ttl
        self.exclude_paths = exclude_paths or {
            '/health',
            '/metrics',
            '/docs',
            '/redoc',
            '/openapi.json'
        }
        self.cache_by_query = cache_by_query
        self.cache_by_auth = cache_by_auth

    def _get_cache_key(self, request: Request) -> str:
        """Generate cache key from request"""
        key_parts = [request.method, request.url.path]
        
        if self.cache_by_query:
            key_parts.append(str(request.query_params))
            
        if self.cache_by_auth:
            auth = request.headers.get('Authorization', '')
            if auth:
                key_parts.append(auth.split()[-1])
                
        return ":".join(key_parts)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method != "GET" or request.url.path in self.exclude_paths:
            return await call_next(request)

        cache_key = self._get_cache_key(request)

        try:
            # Try to get from cache
            cached_response = await self.cache_manager.get(cache_key)
            if cached_response:
                return Response(
                    content=cached_response['content'],
                    status_code=cached_response['status_code'],
                    headers=cached_response['headers'],
                    media_type=cached_response['media_type']
                )

            # Get fresh response
            response = await call_next(request)

            # Cache successful JSON responses
            if (
                response.status_code == 200 and
                response.headers.get('content-type', '').startswith('application/json')
            ):
                await self.cache_manager.set(
                    cache_key,
                    {
                        'content': response.body.decode(),
                        'status_code': response.status_code,
                        'headers': dict(response.headers),
                        'media_type': response.media_type
                    },
                    ttl=self.ttl
                )

            return response

        except Exception as e:
            logger.error(f"Cache middleware error: {str(e)}")
            return await call_next(request) 