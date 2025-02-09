from typing import Dict, Tuple
import time
from threading import Lock
from app.core.config import settings
from app.core.errors import ThrottleError
from app.core.logging import logger

class RequestThrottler:
    def __init__(self):
        self._requests: Dict[str, Dict[str, Tuple[int, float]]] = {}
        self._lock = Lock()
        self._window_size = 60  # 1 minute window
        self._max_requests = settings.MAX_REQUESTS_PER_MINUTE

    def check_throttle(self, client_id: str, endpoint: str) -> None:
        with self._lock:
            now = time.time()
            window_start = now - self._window_size
            
            if client_id not in self._requests:
                self._requests[client_id] = {}
                
            if endpoint not in self._requests[client_id]:
                self._requests[client_id][endpoint] = (1, now)
                return

            count, last_request = self._requests[client_id][endpoint]
            
            # Reset counter if outside window
            if last_request < window_start:
                self._requests[client_id][endpoint] = (1, now)
                return
                
            if count >= self._max_requests:
                wait_time = window_start + self._window_size - now
                logger.warning(
                    f"Request throttled for client {client_id} on endpoint {endpoint}"
                )
                raise ThrottleError(
                    f"Too many requests. Please wait {int(wait_time)} seconds."
                )
                
            self._requests[client_id][endpoint] = (count + 1, now)

    def cleanup(self) -> None:
        with self._lock:
            now = time.time()
            window_start = now - self._window_size
            
            for client_id in list(self._requests.keys()):
                for endpoint in list(self._requests[client_id].keys()):
                    if self._requests[client_id][endpoint][1] < window_start:
                        del self._requests[client_id][endpoint]
                if not self._requests[client_id]:
                    del self._requests[client_id] 