from typing import Any, Dict, Optional, Union
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from app.schemas.responses import SuccessResponse, ErrorResponse
from app.core.context import RequestContext

class ResponseFormatter:
    @staticmethod
    def success(
        data: Any,
        message: Optional[str] = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None
    ) -> JSONResponse:
        context = RequestContext.get_current()
        
        response = SuccessResponse(
            data=data,
            message=message,
            request_id=context.request_id,
            timestamp=datetime.utcnow()
        )

        return JSONResponse(
            status_code=status_code,
            content=response.dict(exclude_none=True),
            headers=headers
        )

    @staticmethod
    def error(
        message: str,
        status_code: int = 400,
        details: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> JSONResponse:
        context = RequestContext.get_current()
        
        response = ErrorResponse(
            message=message,
            details=details,
            request_id=context.request_id,
            timestamp=datetime.utcnow()
        )

        return JSONResponse(
            status_code=status_code,
            content=response.dict(exclude_none=True),
            headers=headers
        )

    @staticmethod
    def paginated(
        data: Any,
        total: int,
        page: int,
        page_size: int,
        message: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> JSONResponse:
        context = RequestContext.get_current()
        
        response = {
            'data': data,
            'pagination': {
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            },
            'request_id': context.request_id,
            'timestamp': datetime.utcnow().isoformat()
        }

        if message:
            response['message'] = message

        return JSONResponse(
            content=response,
            headers=headers
        ) 