from typing import Dict, Any, Optional, Callable
import time
from threading import Lock
from contextlib import contextmanager
from app.core.errors import PoolError
from app.core.logging import logger

class ConnectionPool:
    def __init__(
        self,
        factory: Callable[[], Any],
        min_size: int = 5,
        max_size: int = 10,
        timeout: int = 30
    ):
        self._factory = factory
        self._min_size = min_size
        self._max_size = max_size
        self._timeout = timeout
        
        self._pool: Dict[int, Dict[str, Any]] = {}
        self._in_use: Dict[int, bool] = {}
        self._lock = Lock()
        self._last_cleanup = time.time()
        
        # Initialize pool with minimum connections
        self._initialize_pool()

    def _initialize_pool(self) -> None:
        for _ in range(self._min_size):
            conn = self._create_connection()
            if conn is not None:
                self._pool[id(conn)] = {
                    'connection': conn,
                    'created_at': time.time(),
                    'last_used': time.time()
                }
                self._in_use[id(conn)] = False

    def _create_connection(self) -> Optional[Any]:
        try:
            return self._factory()
        except Exception as e:
            logger.error(f"Failed to create connection: {str(e)}")
            return None

    @contextmanager
    def get_connection(self):
        conn = None
        conn_id = None
        
        try:
            with self._lock:
                # Try to get an available connection
                for cid, in_use in self._in_use.items():
                    if not in_use:
                        conn = self._pool[cid]['connection']
                        conn_id = cid
                        self._in_use[cid] = True
                        self._pool[cid]['last_used'] = time.time()
                        break
                
                # Create new connection if needed and possible
                if conn is None and len(self._pool) < self._max_size:
                    conn = self._create_connection()
                    if conn is not None:
                        conn_id = id(conn)
                        self._pool[conn_id] = {
                            'connection': conn,
                            'created_at': time.time(),
                            'last_used': time.time()
                        }
                        self._in_use[conn_id] = True
                
                if conn is None:
                    raise PoolError("No available connections")
                
            yield conn
            
        finally:
            if conn_id is not None:
                with self._lock:
                    self._in_use[conn_id] = False

    def cleanup(self, max_idle_time: int = 300) -> None:
        with self._lock:
            now = time.time()
            
            # Don't cleanup too frequently
            if now - self._last_cleanup < 60:
                return
                
            self._last_cleanup = now
            
            # Remove idle connections above minimum pool size
            idle_conns = [
                cid for cid, in_use in self._in_use.items()
                if not in_use and 
                now - self._pool[cid]['last_used'] > max_idle_time and
                len(self._pool) > self._min_size
            ]
            
            for cid in idle_conns:
                try:
                    self._pool[cid]['connection'].close()
                except Exception as e:
                    logger.warning(f"Error closing connection: {str(e)}")
                del self._pool[cid]
                del self._in_use[cid] 