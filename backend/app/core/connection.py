from contextlib import contextmanager
from typing import Generator, Any
import socket
import ssl
from app.core.config import settings
from app.core.logging import logger
from app.core.errors import ConnectionError

class ConnectionManager:
    def __init__(self):
        self.timeout = settings.CONNECTION_TIMEOUT
        self.verify_ssl = settings.VERIFY_SSL
        self.max_retries = settings.CONNECTION_MAX_RETRIES

    @contextmanager
    def connect(self, host: str, port: int, use_ssl: bool = True) -> Generator[Any, None, None]:
        sock = None
        try:
            sock = socket.create_connection((host, port), timeout=self.timeout)
            
            if use_ssl:
                context = ssl.create_default_context()
                if not self.verify_ssl:
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname=host)
            
            yield sock
            
        except socket.timeout:
            logger.error(f"Connection timeout to {host}:{port}")
            raise ConnectionError(f"Connection timeout to {host}:{port}")
        except ssl.SSLError as e:
            logger.error(f"SSL error connecting to {host}:{port}: {e}")
            raise ConnectionError(f"SSL error: {e}")
        except Exception as e:
            logger.error(f"Connection error to {host}:{port}: {e}")
            raise ConnectionError(f"Connection failed: {e}")
        finally:
            if sock:
                try:
                    sock.close()
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}") 