"""
Database session management for StrawberryBot.

This module provides an async SQLAlchemy session manager with:
- Connection pooling
- Automatic session cleanup
- Context manager support
- Error handling
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker
)
from sqlalchemy.pool import AsyncAdaptedQueuePool
from src.config.settings import get_config

class DatabaseSessionManager:
    """
    Async SQLAlchemy session manager with connection pooling.
    
    Features:
    - Async/await support
    - Connection pooling
    - Session lifecycle management
    - Error handling and recovery
    - Context manager support
    """
    
    def __init__(self):
        """Initialize the session manager."""
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._config = get_config("database")
    
    async def init(self) -> None:
        """
        Initialize database connection and session factory.
        Should be called before any database operations.
        """
        if not self._engine:
            self._engine = create_async_engine(
                self._config["url"],
                echo=self._config["echo"],
                pool_size=20,
                max_overflow=10,
                poolclass=AsyncAdaptedQueuePool,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False
            )
    
    async def close(self) -> None:
        """
        Close database connections.
        Should be called during shutdown.
        """
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session as an async context manager.
        
        Usage:
            async with db.session() as session:
                result = await session.execute(query)
                
        Yields:
            AsyncSession: Database session
        """
        if not self._session_factory:
            await self.init()
        
        session: AsyncSession = self._session_factory()  # type: ignore
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    @property
    def engine(self) -> AsyncEngine:
        """
        Get the database engine.
        
        Returns:
            AsyncEngine: SQLAlchemy async engine
            
        Raises:
            RuntimeError: If engine is not initialized
        """
        if not self._engine:
            raise RuntimeError("Database engine not initialized")
        return self._engine

# Global database session manager instance
db = DatabaseSessionManager() 