from typing import Dict, Any, List, Optional, Callable
import time
import psutil
import os
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from app.db.session import SessionLocal
from app.core.logging import logger
from app.db.connection import DatabaseManager
from app.core.cache import CacheManager
from enum import Enum
from dataclasses import dataclass, field
from threading import Lock
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
import json

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheck:
    """Health check configuration for a service component"""
    name: str
    check_func: callable
    timeout: float = 5.0
    interval: float = 60.0
    retries: int = 3
    required: bool = True

class HealthManager:
    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        cache_manager: Optional[CacheManager] = None
    ):
        self._checks: Dict[str, HealthCheck] = {}
        self._status: Dict[str, bool] = {}
        self._last_check: Dict[str, float] = {}
        self.start_time = datetime.utcnow()
        self.db_manager = db_manager
        self.cache_manager = cache_manager

    def add_check(self, check: HealthCheck) -> None:
        """Add a health check to the manager"""
        self._checks[check.name] = check
        self._status[check.name] = False
        self._last_check[check.name] = 0

    async def run_check(self, name: str) -> bool:
        """Run a specific health check"""
        check = self._checks[name]
        try:
            for attempt in range(check.retries):
                try:
                    result = await asyncio.wait_for(
                        check.check_func(),
                        timeout=check.timeout
                    )
                    if result:
                        self._status[name] = True
                        return True
                    if attempt < check.retries - 1:
                        await asyncio.sleep(0.5)
                except asyncio.TimeoutError:
                    logger.warning(f"Health check timeout: {name}")
                    continue
            self._status[name] = False
            return False
        except Exception as e:
            logger.error(
                f"Health check failed: {str(e)}",
                extra={'check': name}
            )
            self._status[name] = False
            return False

    async def check_health(self) -> Dict[str, Any]:
        """Run all health checks and return results"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': self._get_uptime(),
            'system': await self._check_system(),
            'checks': {}
        }
        
        overall_status = True

        # Run component checks
        for name, check in self._checks.items():
            status = await self.run_check(name)
            results['checks'][name] = {
                'status': 'healthy' if status else 'unhealthy',
                'required': check.required
            }
            if check.required and not status:
                overall_status = False

        # Add database and cache status if available
        if self.db_manager:
            results['database'] = await self._check_database()
            if results['database']['status'] == 'unhealthy':
                overall_status = False

        if self.cache_manager:
            results['cache'] = await self._check_cache()
            if results['cache']['status'] == 'unhealthy':
                overall_status = False

        results['status'] = 'healthy' if overall_status else 'unhealthy'
        return results

    def _get_uptime(self) -> float:
        """Get service uptime in seconds"""
        return (datetime.utcnow() - self.start_time).total_seconds()

    async def _check_system(self) -> Dict[str, Any]:
        """Check system resources"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            process = psutil.Process(os.getpid())
            
            return {
                'status': 'healthy',
                'cpu': {
                    'percent': cpu_percent,
                    'cores': psutil.cpu_count()
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'process_rss': process.memory_info().rss / 1024 / 1024,  # MB
                    'process_vms': process.memory_info().vms / 1024 / 1024   # MB
                },
                'disk': {
                    'total': disk.total,
                    'free': disk.free,
                    'percent': disk.percent
                }
            }
        except Exception as e:
            logger.error(f"System health check failed: {str(e)}")
            return {'status': 'unhealthy', 'error': str(e)}

    async def _check_database(self) -> Dict[str, Any]:
        """Check database connection"""
        try:
            is_connected = await self.db_manager.check_connection()
            return {
                'status': 'healthy' if is_connected else 'unhealthy',
                'connected': is_connected
            }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {'status': 'unhealthy', 'error': str(e)}

    async def _check_cache(self) -> Dict[str, Any]:
        """Check cache connection"""
        try:
            test_key = '_health_check_test'
            test_value = datetime.utcnow().isoformat()
            
            await self.cache_manager.set(test_key, test_value, ttl=60)
            retrieved_value = await self.cache_manager.get(test_key)
            await self.cache_manager.delete(test_key)
            
            return {
                'status': 'healthy' if retrieved_value == test_value else 'unhealthy',
                'working': retrieved_value == test_value
            }
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")
            return {'status': 'unhealthy', 'error': str(e)}

class HealthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        health_manager: Optional[HealthManager] = None,
        health_path: str = '/health',
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.health_manager = health_manager or HealthManager()
        self.health_path = health_path
        self.exclude_paths = exclude_paths or {
            '/metrics',
            '/docs',
            '/redoc',
            '/openapi.json'
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            # Handle health check requests
            if request.url.path == self.health_path:
                results = await self.health_manager.check_health()
                status_code = 200 if results['status'] == 'healthy' else 503
                return Response(
                    content=json.dumps(results),
                    status_code=status_code,
                    media_type='application/json'
                )

            # Skip health checks for excluded paths
            if request.url.path in self.exclude_paths:
                return await call_next(request)

            # Check health before processing request
            health_status = await self.health_manager.check_health()
            if health_status['status'] != 'healthy':
                return Response(
                    content=json.dumps({
                        'error': 'Service unhealthy',
                        'details': health_status
                    }),
                    status_code=503,
                    media_type='application/json'
                )

            return await call_next(request)
            
        except Exception as e:
            logger.error(f"Error in health middleware: {str(e)}")
            return await call_next(request)

# Example health checks
def check_database_connection() -> bool:
    try:
        # Add your database connection check here
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False

def check_cache_connection() -> bool:
    try:
        # Add your cache connection check here
        return True
    except Exception as e:
        logger.error(f"Cache health check failed: {str(e)}")
        return False

def check_disk_space() -> bool:
    try:
        # Add your disk space check here
        return True
    except Exception as e:
        logger.error(f"Disk space check failed: {str(e)}")
        return False

# Initialize health monitor with checks
health_manager = HealthManager()

# Database health check
async def check_database():
    try:
        await db.execute('SELECT 1')
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False

health_manager.add_check(
    HealthCheck(
        name='database',
        check_func=check_database,
        timeout=5.0,
        interval=30.0,
        required=True
    )
)

# Redis health check
async def check_redis():
    try:
        await redis.ping()
        return True
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return False

health_manager.add_check(
    HealthCheck(
        name='redis',
        check_func=check_redis,
        timeout=2.0,
        interval=15.0,
        required=False
    )
)

# Add middleware to FastAPI app
app.add_middleware(
    HealthMiddleware,
    health_manager=health_manager
) 