from typing import Dict, Any, Optional, AsyncGenerator
import time
from uuid import uuid4
from datetime import datetime
from threading import Lock
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger
from app.core.errors import SessionError
from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    echo=settings.DB_ECHO
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

class SessionManager:
    """Manages both database and user sessions"""
    
    def __init__(
        self,
        session_timeout: int = 3600,
        cleanup_interval: int = 300
    ):
        # Database session management
        self.engine = engine
        self.session_factory = AsyncSessionLocal
        
        # User session management
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self._session_timeout = session_timeout
        self._last_cleanup = time.time()
        self._cleanup_interval = cleanup_interval

    # Database session methods
    @asynccontextmanager
    async def get_db_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session with automatic cleanup"""
        session: Optional[AsyncSession] = None
        try:
            session = self.session_factory()
            yield session
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            if session:
                await session.rollback()
            raise
        finally:
            if session:
                await session.close()

    async def cleanup_db(self) -> None:
        """Cleanup database connections"""
        try:
            await self.engine.dispose()
        except Exception as e:
            logger.error(f"Error cleaning up database connections: {str(e)}")

    # User session methods
    def create_user_session(self, user_id: str) -> str:
        """Create a new user session"""
        session_id = str(uuid4())
        
        with self._lock:
            self._cleanup_expired()
            self._sessions[session_id] = {
                'user_id': user_id,
                'created_at': datetime.utcnow(),
                'last_accessed': datetime.utcnow(),
                'data': {}
            }
            
        return session_id

    def get_user_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get user session data"""
        with self._lock:
            self._cleanup_expired()
            
            if session_id not in self._sessions:
                return None
                
            session = self._sessions[session_id]
            if self._is_expired(session):
                del self._sessions[session_id]
                return None
                
            session['last_accessed'] = datetime.utcnow()
            return session.copy()

    def update_user_session(
        self,
        session_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Update user session data"""
        with self._lock:
            if session_id not in self._sessions:
                raise SessionError("Session not found")
                
            session = self._sessions[session_id]
            if self._is_expired(session):
                del self._sessions[session_id]
                raise SessionError("Session expired")
                
            session['data'].update(data)
            session['last_accessed'] = datetime.utcnow()

    def delete_user_session(self, session_id: str) -> None:
        """Delete a user session"""
        with self._lock:
            self._sessions.pop(session_id, None)

    def _is_expired(self, session: Dict[str, Any]) -> bool:
        """Check if a session is expired"""
        last_accessed = session['last_accessed']
        return (datetime.utcnow() - last_accessed).total_seconds() > self._session_timeout

    def _cleanup_expired(self) -> None:
        """Clean up expired sessions"""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        try:
            expired_sessions = [
                session_id
                for session_id, session in self._sessions.items()
                if self._is_expired(session)
            ]
            for session_id in expired_sessions:
                del self._sessions[session_id]
                
            self._last_cleanup = now
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {str(e)}")

class SessionMiddleware(BaseHTTPMiddleware):
    """Middleware for managing sessions per request"""
    
    def __init__(
        self,
        app,
        session_manager: Optional[SessionManager] = None,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.session_manager = session_manager or SessionManager()
        self.exclude_paths = exclude_paths or {
            '/health',
            '/metrics',
            '/docs',
            '/redoc',
            '/openapi.json'
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        async with self.session_manager.get_db_session() as session:
            try:
                # Add database session to request state
                request.state.db = session
                
                # Handle user session if present
                session_id = request.cookies.get('session_id')
                if session_id:
                    user_session = self.session_manager.get_user_session(session_id)
                    if user_session:
                        request.state.user_session = user_session
                
                response = await call_next(request)
                
                # Commit if no errors occurred
                if response.status_code < 400:
                    await session.commit()
                else:
                    await session.rollback()
                    
                return response
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Session middleware error: {str(e)}")
                return Response(
                    content="Internal server error",
                    status_code=500
                )

# Helper functions
async def get_db(request: Request) -> AsyncSession:
    """Get database session from request state"""
    return request.state.db

def get_user_session(request: Request) -> Optional[Dict[str, Any]]:
    """Get user session from request state"""
    return getattr(request.state, 'user_session', None)

# Database session dependency
@asynccontextmanager
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session"""
    async with SessionManager().get_db_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise 