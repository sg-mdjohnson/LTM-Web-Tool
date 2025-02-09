from typing import Dict, Optional, Any, List
import time
import cProfile
import pstats
import io
from functools import wraps
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

class Profiler:
    def __init__(self):
        self._profiler = cProfile.Profile()
        self._stats: Optional[pstats.Stats] = None
        self._start_time: float = 0
        self._end_time: float = 0

    def start(self) -> None:
        self._start_time = time.time()
        self._profiler.enable()

    def stop(self) -> None:
        self._profiler.disable()
        self._end_time = time.time()
        self._stats = pstats.Stats(self._profiler)
        self._stats.sort_stats('cumulative')

    def get_stats(self, top_n: int = 10) -> Dict[str, Any]:
        if not self._stats:
            return {}

        # Redirect stdout to capture stats output
        output = io.StringIO()
        self._stats.stream = output
        self._stats.print_stats(top_n)
        
        stats_str = output.getvalue()
        output.close()

        return {
            'duration': self._end_time - self._start_time,
            'stats': stats_str,
            'top_functions': self._get_top_functions(top_n)
        }

    def _get_top_functions(self, limit: int) -> List[Dict[str, Any]]:
        if not self._stats:
            return []

        functions = []
        for func_stats in self._stats.stats.items():
            ((file_name, line_number, func_name), (cc, nc, tt, ct, callers)) = func_stats
            functions.append({
                'file': file_name,
                'line': line_number,
                'function': func_name,
                'calls': cc,
                'time': tt,
                'cumulative_time': ct
            })

        return sorted(
            functions,
            key=lambda x: x['cumulative_time'],
            reverse=True
        )[:limit]

def profile(func):
    """Decorator to profile a function"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        profiler = Profiler()
        profiler.start()
        
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            profiler.stop()
            stats = profiler.get_stats()
            logger.info(
                f"Function profile: {func.__name__}",
                extra={'profile_stats': stats}
            )

    return wrapper

class ProfilerMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        enable_profiling: bool = False,
        profile_paths: Optional[set] = None,
        min_duration: float = 1.0
    ):
        super().__init__(app)
        self.enable_profiling = enable_profiling
        self.profile_paths = profile_paths or set()
        self.min_duration = min_duration

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.enable_profiling:
            return await call_next(request)

        path = request.url.path
        if self.profile_paths and path not in self.profile_paths:
            return await call_next(request)

        profiler = Profiler()
        profiler.start()

        try:
            response = await call_next(request)
            return response
            
        finally:
            profiler.stop()
            stats = profiler.get_stats()
            
            if stats.get('duration', 0) >= self.min_duration:
                logger.info(
                    f"Request profile: {request.method} {path}",
                    extra={
                        'profile_stats': stats,
                        'request_method': request.method,
                        'request_path': path
                    }
                )

class EndpointProfiler:
    def __init__(self):
        self._profiles: Dict[str, List[Dict[str, Any]]] = {}
        self._max_profiles = 100  # Keep last 100 profiles per endpoint

    def add_profile(self, endpoint: str, profile_data: Dict[str, Any]) -> None:
        if endpoint not in self._profiles:
            self._profiles[endpoint] = []
            
        profiles = self._profiles[endpoint]
        profiles.append(profile_data)
        
        # Keep only the last max_profiles
        if len(profiles) > self._max_profiles:
            profiles.pop(0)

    def get_profiles(
        self,
        endpoint: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        if endpoint:
            if endpoint not in self._profiles:
                return {}
            return {
                'endpoint': endpoint,
                'profiles': self._profiles[endpoint][-limit:]
            }

        return {
            endpoint: profiles[-limit:]
            for endpoint, profiles in self._profiles.items()
        }

    def get_summary(self, endpoint: str) -> Dict[str, Any]:
        if endpoint not in self._profiles:
            return {}

        profiles = self._profiles[endpoint]
        durations = [p['duration'] for p in profiles]
        
        return {
            'endpoint': endpoint,
            'count': len(profiles),
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'last_profile': profiles[-1] if profiles else None
        } 