from typing import AsyncGenerator, Optional, Dict, Any
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.logging import logger

class DatabaseManager:
    """Manages database connections and sessions"""

    def __init__(
        self,
        db_url: Optional[str] = None,
        pool_size: Optional[int] = None,
        max_overflow: Optional[int] = None,
        pool_timeout: int = 30,
        echo: bool = False
    ):
        self.db_url = db_url or settings.SQLALCHEMY_DATABASE_URI
        self.pool_size = pool_size or settings.DB_POOL_SIZE
        self.max_overflow = max_overflow or settings.DB_MAX_OVERFLOW
        self.pool_timeout = pool_timeout
        self.echo = echo
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    async def init(self) -> None:
        """Initialize database connection"""
        try:
            if not self._engine:
                self._engine = create_async_engine(
                    self.db_url,
                    poolclass=AsyncAdaptedQueuePool,
                    pool_pre_ping=True,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_timeout=self.pool_timeout,
                    echo=self.echo
                )

                self._session_factory = async_sessionmaker(
                    self._engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autocommit=False,
                    autoflush=False
                )

        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise

    async def close(self) -> None:
        """Close database connection"""
        if self._engine:
            try:
                await self._engine.dispose()
                self._engine = None
                self._session_factory = None
            except Exception as e:
                logger.error(f"Database close error: {str(e)}")
                raise

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with automatic cleanup"""
        if not self._session_factory:
            await self.init()

        session: Optional[AsyncSession] = None
        try:
            session = self._session_factory()
            yield session
        except SQLAlchemyError as e:
            logger.error(f"Database session error: {str(e)}")
            if session:
                await session.rollback()
            raise
        finally:
            if session:
                await session.close()

    async def check_connection(self) -> bool:
        """Check database connection health"""
        try:
            if not self._engine:
                await self.init()

            async with self._engine.connect() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {str(e)}")
            return False

    async def get_pool_status(self) -> Dict[str, Any]:
        """Get connection pool status"""
        if not self._engine:
            return {
                "status": "not_initialized",
                "pool_size": 0,
                "connections_in_use": 0,
                "connections_available": 0
            }

        try:
            pool = self._engine.pool
            return {
                "status": "active",
                "pool_size": pool.size(),
                "connections_in_use": pool.checkedin(),
                "connections_available": pool.checkedout(),
                "overflow": pool.overflow()
            }
        except Exception as e:
            logger.error(f"Error getting pool status: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def reset_pool(self) -> bool:
        """Reset connection pool"""
        try:
            if self._engine:
                await self._engine.dispose()
                await self.init()
            return True
        except Exception as e:
            logger.error(f"Error resetting connection pool: {str(e)}")
            return False

# Global database manager instance
db_manager = DatabaseManager()

# Dependency for database session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session"""
    async with db_manager.session() as session:
        yield session

# Context manager for database transactions
@asynccontextmanager
async def transaction(session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database transactions"""
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise 