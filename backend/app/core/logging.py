import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for logs"""
    
    def __init__(self, **kwargs):
        self.default_fields = kwargs.pop('default_fields', {})
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add default fields
        log_data.update(self.default_fields)

        # Add extra fields from record
        if hasattr(record, 'extra'):
            log_data.update(record.extra)

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }

        return json.dumps(log_data)

class RequestIdFilter(logging.Filter):
    """Filter that adds request ID to log records"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, 'request_id'):
            record.request_id = 'no_request'
        return True

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    json_format: bool = True
) -> logging.Logger:
    """Setup application logging"""
    
    # Create logger
    logger = logging.getLogger('app')
    logger.setLevel(log_level)
    logger.addFilter(RequestIdFilter())

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatters
    if json_format:
        formatter = JSONFormatter(
            default_fields={
                'app_name': settings.APP_NAME,
                'environment': settings.ENVIRONMENT
            }
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(request_id)s - %(message)s'
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if log file specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Use RotatingFileHandler for size-based rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Add daily rotation handler
        daily_handler = TimedRotatingFileHandler(
            log_file + '.daily',
            when='midnight',
            interval=1,
            backupCount=30
        )
        daily_handler.setFormatter(formatter)
        logger.addHandler(daily_handler)

    return logger

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging"""
    
    def __init__(
        self,
        app,
        logger: Optional[logging.Logger] = None,
        exclude_paths: Optional[set] = None,
        log_request_body: bool = False
    ):
        super().__init__(app)
        self.logger = logger or logging.getLogger('app')
        self.exclude_paths = exclude_paths or {
            '/health',
            '/metrics',
            '/docs',
            '/redoc',
            '/openapi.json'
        }
        self.log_request_body = log_request_body

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        start_time = datetime.utcnow()
        request_id = request.headers.get('X-Request-ID', 'unknown')
        
        # Log request
        log_data = {
            'request_id': request_id,
            'method': request.method,
            'path': request.url.path,
            'query_params': dict(request.query_params),
            'client_ip': request.client.host,
            'user_agent': request.headers.get('user-agent'),
        }

        if self.log_request_body and request.method in ('POST', 'PUT', 'PATCH'):
            try:
                body = await request.json()
                log_data['body'] = body
            except:
                pass

        self.logger.info(
            f"Request {request.method} {request.url.path}",
            extra=log_data
        )

        try:
            response = await call_next(request)
            
            # Log response
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.info(
                f"Response {response.status_code}",
                extra={
                    'request_id': request_id,
                    'status_code': response.status_code,
                    'duration': duration
                }
            )
            
            return response
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.error(
                f"Request failed: {str(e)}",
                extra={
                    'request_id': request_id,
                    'error': str(e),
                    'duration': duration
                },
                exc_info=True
            )
            raise

# Initialize logger
logger = setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file=settings.LOG_FILE,
    json_format=settings.LOG_JSON_FORMAT
) 