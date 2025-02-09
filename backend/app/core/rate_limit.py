from typing import Dict, Tuple
import time
from threading import Lock
from app.core.config import settings
from app.core.errors import RateLimitError

class RateLimiter:
    def __init__(self):
        self._requests: Dict[str, Dict[str, Tuple[int, float]]] = {}
        self._lock = Lock()
        self._cleanup_interval = 3600  # Cleanup every hour

    def check_rate_limit(self, client_id: str, endpoint: str) -> None:
        with self._lock:
            self._cleanup_old_records()
            
            now = time.time()
            window_start = now - 60  # 1 minute window
            
            if client_id not in self._requests:
                self._requests[client_id] = {}
            
            if endpoint not in self._requests[client_id]:
                self._requests[client_id][endpoint] = (1, now)
                return
            
            count, last_request = self._requests[client_id][endpoint]
            
            if last_request < window_start:
                self._requests[client_id][endpoint] = (1, now)
                return
                
            if count >= settings.RATE_LIMIT_PER_MINUTE:
                raise RateLimitError(
                    f"Rate limit exceeded for endpoint {endpoint}"
                )
                
            self._requests[client_id][endpoint] = (count + 1, now)

    def _cleanup_old_records(self) -> None:
        now = time.time()
        window_start = now - 60
        
        for client_id in list(self._requests.keys()):
            for endpoint in list(self._requests[client_id].keys()):
                if self._requests[client_id][endpoint][1] < window_start:
                    del self._requests[client_id][endpoint]
            if not self._requests[client_id]:
                del self._requests[client_id] 