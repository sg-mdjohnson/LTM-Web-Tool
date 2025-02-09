from typing import Optional, Any, Dict, List
from pydantic import BaseModel
from datetime import datetime

class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str
    code: Optional[str] = None

class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime = datetime.utcnow()
    request_id: Optional[str] = None

class SuccessResponse(BaseModel):
    status: str = "success"
    data: Any
    message: Optional[str] = None
    timestamp: datetime = datetime.utcnow()
    request_id: Optional[str] = None

class PaginatedResponse(SuccessResponse):
    total: int
    page: int
    page_size: int
    next_page: Optional[int] = None
    previous_page: Optional[int] = None 