from typing import Dict, Optional, Any, List, Union, Callable
import asyncio
from dataclasses import dataclass, field
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

@dataclass
class BatchConfig:
    max_size: int  # Maximum batch size
    timeout: float  # Maximum wait time in seconds
    processor: Callable  # Function to process batch
    key_func: Optional[Callable[[Request], str]] = None

class BatchProcessor:
    def __init__(self):
        self._configs: Dict[str, BatchConfig] = {}
        self._batches: Dict[str, Dict[str, List[Any]]] = {}
        self._events: Dict[str, Dict[str, asyncio.Event]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._tasks: Dict[str, Dict[str, asyncio.Task]] = {}

    def add_config(
        self,
        path: str,
        method: str,
        config: BatchConfig
    ) -> None:
        key = f"{method.upper()} {path}"
        self._configs[key] = config
        self._batches[key] = {}
        self._events[key] = {}
        self._locks[key] = asyncio.Lock()
        self._tasks[key] = {}

    def _get_batch_key(self, request: Request, config: BatchConfig) -> str:
        if config.key_func:
            return config.key_func(request)
        return 'default'

    async def process_batch(
        self,
        endpoint_key: str,
        batch_key: str
    ) -> None:
        try:
            async with self._locks[endpoint_key]:
                batch = self._batches[endpoint_key].pop(batch_key, [])
                if batch:
                    config = self._configs[endpoint_key]
                    await config.processor(batch)
        except Exception as e:
            logger.error(
                f"Error processing batch: {str(e)}",
                extra={'endpoint': endpoint_key, 'batch_key': batch_key}
            )
        finally:
            if batch_key in self._events[endpoint_key]:
                self._events[endpoint_key][batch_key].set()

    async def add_to_batch(
        self,
        request: Request,
        item: Any
    ) -> None:
        endpoint_key = f"{request.method.upper()} {request.url.path}"
        if endpoint_key not in self._configs:
            return

        config = self._configs[endpoint_key]
        batch_key = self._get_batch_key(request, config)

        async with self._locks[endpoint_key]:
            if batch_key not in self._batches[endpoint_key]:
                self._batches[endpoint_key][batch_key] = []
                self._events[endpoint_key][batch_key] = asyncio.Event()
                
                # Schedule batch processing
                self._tasks[endpoint_key][batch_key] = asyncio.create_task(
                    self._schedule_batch(endpoint_key, batch_key)
                )

            batch = self._batches[endpoint_key][batch_key]
            batch.append(item)

            if len(batch) >= config.max_size:
                await self.process_batch(endpoint_key, batch_key)

    async def _schedule_batch(
        self,
        endpoint_key: str,
        batch_key: str
    ) -> None:
        try:
            config = self._configs[endpoint_key]
            await asyncio.sleep(config.timeout)
            await self.process_batch(endpoint_key, batch_key)
        except Exception as e:
            logger.error(f"Error scheduling batch: {str(e)}")

    async def wait_for_batch(
        self,
        request: Request
    ) -> None:
        endpoint_key = f"{request.method.upper()} {request.url.path}"
        if endpoint_key not in self._configs:
            return

        config = self._configs[endpoint_key]
        batch_key = self._get_batch_key(request, config)

        if batch_key in self._events[endpoint_key]:
            await self._events[endpoint_key][batch_key].wait()

class BatchingMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        processor: Optional[BatchProcessor] = None,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.processor = processor or BatchProcessor()
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
            # Add request to batch if it's a POST request
            if request.method == 'POST':
                body_bytes = await request.body()
                if body_bytes:
                    import json
                    try:
                        body = json.loads(body_bytes)
                        await self.processor.add_to_batch(request, body)
                        await self.processor.wait_for_batch(request)
                    except json.JSONDecodeError:
                        pass

            return await call_next(request)
            
        except Exception as e:
            logger.error(f"Error in request batching: {str(e)}")
            return await call_next(request)

# Example usage:
"""
processor = BatchProcessor()

# Add batch configuration for bulk operations
async def process_user_batch(batch: List[Dict[str, Any]]) -> None:
    # Process batch of user creations
    async with db_session() as session:
        users = [User(**item) for item in batch]
        session.add_all(users)
        await session.commit()

processor.add_config(
    "/api/users/bulk",
    "POST",
    BatchConfig(
        max_size=100,  # Process in batches of 100
        timeout=5.0,   # Or after 5 seconds
        processor=process_user_batch
    )
)

# Add middleware to FastAPI app
app.add_middleware(
    BatchingMiddleware,
    processor=processor
)
""" 