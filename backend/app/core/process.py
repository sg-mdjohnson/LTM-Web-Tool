import os
import signal
import psutil
from typing import List, Optional
from datetime import datetime
from app.core.logging import logger

class ProcessManager:
    def __init__(self):
        self.pid = os.getpid()
        self.process = psutil.Process(self.pid)
        self._shutdown_handlers = []

    def register_shutdown_handler(self, handler):
        self._shutdown_handlers.append(handler)

    def setup_signal_handlers(self):
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown")
        for handler in self._shutdown_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Error in shutdown handler: {e}")
        os._exit(0)

    def get_resource_usage(self):
        try:
            return {
                'cpu_percent': self.process.cpu_percent(),
                'memory_percent': self.process.memory_percent(),
                'num_threads': self.process.num_threads(),
                'open_files': len(self.process.open_files()),
                'connections': len(self.process.connections()),
                'io_counters': self.process.io_counters()._asdict(),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting resource usage: {e}")
            return None

    def cleanup_zombie_processes(self):
        try:
            children = self.process.children(recursive=True)
            for child in children:
                if child.status() == psutil.STATUS_ZOMBIE:
                    logger.warning(f"Cleaning up zombie process {child.pid}")
                    child.kill()
        except Exception as e:
            logger.error(f"Error cleaning up zombie processes: {e}") 