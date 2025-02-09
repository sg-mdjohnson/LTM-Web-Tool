from typing import Generator, Dict, Any, Optional, Type, TypeVar, Callable
from functools import wraps
import inspect
from fastapi import Depends, Request
from sqlalchemy.orm import Session
from app.db.connection import DatabaseManager
from app.core.cache import Cache
from app.core.metrics import MetricsCollector
from app.core.rate_limit import RateLimiter
from app.core.tracing import RequestTracer
from app.core.config import settings
from app.core.logging import logger

T = TypeVar('T')

class DependencyContainer:
    def __init__(self):
        self._dependencies: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[..., Any]] = {}
        self._singletons: Dict[str, Any] = {}

    def register(
        self,
        interface: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[..., T]] = None,
        singleton: bool = False
    ) -> None:
        """Register a dependency"""
        key = self._get_key(interface)

        if implementation and factory:
            raise ValueError(
                "Cannot specify both implementation and factory"
            )

        if factory:
            self._factories[key] = factory
        elif implementation:
            if singleton:
                self._singletons[key] = implementation
            else:
                self._dependencies[key] = implementation
        else:
            raise ValueError(
                "Must specify either implementation or factory"
            )

    def resolve(self, interface: Type[T]) -> T:
        """Resolve a dependency"""
        key = self._get_key(interface)

        # Check singletons first
        if key in self._singletons:
            if key not in self._dependencies:
                self._dependencies[key] = self._singletons[key]()
            return self._dependencies[key]

        # Then check factories
        if key in self._factories:
            return self._factories[key]()

        # Finally check regular dependencies
        if key in self._dependencies:
            return self._dependencies[key]()

        raise KeyError(f"No dependency registered for {interface}")

    def _get_key(self, interface: Type[T]) -> str:
        return f"{interface.__module__}.{interface.__name__}"

class Inject:
    def __init__(self, container: DependencyContainer):
        self.container = container

    def __call__(self, cls: Type[T]) -> Type[T]:
        """Class decorator for dependency injection"""
        original_init = cls.__init__

        @wraps(original_init)
        def new_init(self, *args, **kwargs):
            # Get constructor parameters
            sig = inspect.signature(original_init)
            params = sig.parameters

            # Inject dependencies for annotated parameters
            for name, param in params.items():
                if (
                    name != 'self' and
                    name not in kwargs and
                    param.annotation != inspect.Parameter.empty
                ):
                    try:
                        kwargs[name] = self.container.resolve(param.annotation)
                    except KeyError:
                        # Skip if dependency not found
                        pass

            original_init(self, *args, **kwargs)

        cls.__init__ = new_init
        return cls

def inject_dependencies(container: DependencyContainer):
    """Dependency injection for FastAPI dependencies"""
    def dependency(request: Request):
        return container

    return Depends(dependency)

class Dependencies:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.cache = Cache()
        self.metrics = MetricsCollector()
        self.rate_limiter = RateLimiter()
        
    def get_db(self) -> Generator[Session, None, None]:
        with self.db_manager.get_session() as session:
            yield session

    def get_cache(self) -> Cache:
        return self.cache

    def get_metrics(self) -> MetricsCollector:
        return self.metrics

    def get_rate_limiter(self) -> RateLimiter:
        return self.rate_limiter

    def get_tracer(self, request: Request) -> RequestTracer:
        return RequestTracer()

dependencies = Dependencies()

def get_db() -> Generator[Session, None, None]:
    return dependencies.get_db()

def get_cache() -> Cache:
    return dependencies.get_cache()

def get_metrics() -> MetricsCollector:
    return dependencies.get_metrics()

def get_rate_limiter() -> RateLimiter:
    return dependencies.get_rate_limiter()

def get_tracer(request: Request) -> RequestTracer:
    return dependencies.get_tracer(request)

# Example usage:
"""
from typing import Protocol

class Database(Protocol):
    def connect(self) -> None: ...
    def query(self, sql: str) -> Any: ...

class PostgresDatabase:
    def connect(self) -> None:
        # Implementation
        pass

    def query(self, sql: str) -> Any:
        # Implementation
        pass

container = DependencyContainer()
container.register(Database, PostgresDatabase, singleton=True)

@Inject(container)
class UserService:
    def __init__(self, db: Database):
        self.db = db

# In FastAPI app:
app.dependency_overrides[inject_dependencies] = lambda: container
""" 