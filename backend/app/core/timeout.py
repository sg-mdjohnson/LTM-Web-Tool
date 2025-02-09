from functools import wraps
import asyncio
from fastapi import HTTPException
from app.core.config import settings

class TimeoutError(HTTPException):
    def __init__(self, detail: str = "Request timeout"):
        super().__init__(status_code=408, detail=detail)

def timeout_handler(seconds: int = None):
    if seconds is None:
        seconds = settings.DEFAULT_TIMEOUT

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                raise TimeoutError()
        return wrapper
    return decorator 