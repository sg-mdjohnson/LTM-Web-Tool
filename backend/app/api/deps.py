from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.errors import AuthenticationError, PermissionError
import time

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_api_key(request: Request) -> None:
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise AuthenticationError("API key is required")
    # Add your API key validation logic here

def rate_limit(request: Request) -> None:
    # Basic rate limiting
    now = time.time()
    client_ip = request.client.host
    # Implement rate limiting logic here 