from typing import Any, Dict, List, Optional, Union
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from app.core.context import RequestContext

class ResponseFormatter:
    @staticmethod
    def success(
        data: Any,
        message: Optional[str] = None,
        status_code: int = 200,
        metadata: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> JSONResponse:
        context = RequestContext.get_current()
        
        response = {
            'success': True,
            'data': data,
            'request_id': context.request_id,
            'timestamp': datetime.utcnow().isoformat()
        }

        if message:
            response['message'] = message
            
        if metadata:
            response['metadata'] = metadata

        return JSONResponse(
            status_code=status_code,
            content=response,
            headers=headers
        )

    @staticmethod
    def error(
        message: str,
        status_code: int = 400,
        error_code: Optional[str] = None,
        details: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> JSONResponse:
        context = RequestContext.get_current()
        
        response = {
            'success': False,
            'message': message,
            'request_id': context.request_id,
            'timestamp': datetime.utcnow().isoformat()
        }

        if error_code:
            response['error_code'] = error_code
            
        if details:
            response['details'] = details

        return JSONResponse(
            status_code=status_code,
            content=response,
            headers=headers
        )

    @staticmethod
    def paginated(
        data: List[Any],
        total: int,
        page: int,
        page_size: int,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> JSONResponse:
        context = RequestContext.get_current()
        
        total_pages = (total + page_size - 1) // page_size
        
        response = {
            'success': True,
            'data': data,
            'pagination': {
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            },
            'request_id': context.request_id,
            'timestamp': datetime.utcnow().isoformat()
        }

        if message:
            response['message'] = message
            
        if metadata:
            response['metadata'] = metadata

        return JSONResponse(
            content=response,
            headers=headers
        ) 