from typing import Any, Dict, Optional, List, Union
from datetime import datetime
from fastapi import Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.core.logging import logger

class APIResponse(BaseModel):
    """Base API response model"""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    errors: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0"
    }

class ResponseFormatter:
    """Handles API response formatting"""

    @staticmethod
    def success(
        data: Any = None,
        message: Optional[str] = None,
        status_code: int = 200,
        metadata: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """Format successful response"""
        response_data = APIResponse(
            success=True,
            message=message,
            data=data,
            metadata={
                **APIResponse.__fields__['metadata'].default,
                **(metadata or {})
            }
        )

        return JSONResponse(
            content=response_data.dict(),
            status_code=status_code
        )

    @staticmethod
    def error(
        message: str,
        errors: Optional[List[Dict[str, Any]]] = None,
        status_code: int = 400,
        metadata: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """Format error response"""
        response_data = APIResponse(
            success=False,
            message=message,
            errors=errors,
            metadata={
                **APIResponse.__fields__['metadata'].default,
                **(metadata or {})
            }
        )

        return JSONResponse(
            content=response_data.dict(),
            status_code=status_code
        )

    @staticmethod
    def paginated(
        data: List[Any],
        total: int,
        page: int,
        page_size: int,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """Format paginated response"""
        response_data = APIResponse(
            success=True,
            message=message,
            data=data,
            metadata={
                **APIResponse.__fields__['metadata'].default,
                **(metadata or {}),
                "pagination": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }
        )

        return JSONResponse(
            content=response_data.dict(),
            status_code=200
        )

    @staticmethod
    def stream(
        data: Any,
        content_type: str = "application/octet-stream"
    ) -> Response:
        """Format streaming response"""
        return Response(
            content=data,
            media_type=content_type
        )

# Example usage:
"""
@app.get("/api/users")
async def get_users(
    page: int = 1,
    page_size: int = 10
):
    try:
        users = await user_service.get_users(page, page_size)
        total = await user_service.get_total_users()
        
        return ResponseFormatter.paginated(
            data=users,
            total=total,
            page=page,
            page_size=page_size,
            message="Users retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return ResponseFormatter.error(
            message="Failed to retrieve users",
            errors=[{"detail": str(e)}],
            status_code=500
        )

@app.get("/api/files/{file_id}")
async def download_file(file_id: str):
    try:
        file_data = await file_service.get_file(file_id)
        return ResponseFormatter.stream(
            data=file_data,
            content_type="application/pdf"
        )
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return ResponseFormatter.error(
            message="Failed to download file",
            errors=[{"detail": str(e)}],
            status_code=500
        )
""" 