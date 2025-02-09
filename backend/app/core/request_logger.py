from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
from datetime import datetime
from app.core.logging import logger
from app.core.context import RequestContext

class RequestLogger:
    @staticmethod
    def log_request(
        request: Request,
        response: Optional[Response] = None,
        error: Optional[Exception] = None,
        duration: Optional[float] = None
    ) -> None:
        context = RequestContext.get_current()
        
        log_data = {
            'request_id': context.request_id,
            'method': request.method,
            'path': str(request.url.path),
            'query_params': dict(request.query_params),
            'client_ip': request.client.host,
            'user_agent': request.headers.get('user-agent'),
            'timestamp': datetime.utcnow().isoformat(),
            'duration_ms': round(duration * 1000) if duration else None
        }

        if response:
            log_data.update({
                'status_code': response.status_code,
                'response_size': len(response.body) if hasattr(response, 'body') else None
            })

        if error:
            log_data.update({
                'error': str(error),
                'error_type': error.__class__.__name__
            })

        if context.user_id:
            log_data['user_id'] = context.user_id

        # Add custom tags
        log_data.update(context.get_all_tags())

        # Log at appropriate level based on status code or error
        if error or (response and response.status_code >= 500):
            logger.error("Request failed", extra=log_data)
        elif response and response.status_code >= 400:
            logger.warning("Request failed", extra=log_data)
        else:
            logger.info("Request completed", extra=log_data)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        error = None
        response = None

        try:
            response = await call_next(request)
            return response
            
        except Exception as e:
            error = e
            raise
            
        finally:
            duration = time.time() - start_time
            RequestLogger.log_request(
                request,
                response=response,
                error=error,
                duration=duration
            ) 