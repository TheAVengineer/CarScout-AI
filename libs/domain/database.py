"""
Database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from configs.settings import settings

# Async engine for FastAPI
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_size=20,  # Increased from default 5
    max_overflow=40,  # Increased from default 10
    pool_pre_ping=True,  # Test connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Async session factory
async_session_factory = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Sync engine for Celery workers (higher pool for many workers)
sync_engine = create_engine(
    settings.DATABASE_SYNC_URL,
    echo=settings.DEBUG,
    future=True,
    pool_size=30,  # Much larger for Celery workers
    max_overflow=50,  # Allow bursts of connections
    pool_pre_ping=True,  # Test connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Sync session factory
sync_session_factory = sessionmaker(
    sync_engine,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncSession:
    """
    Dependency for FastAPI to get async database session
    """
    async with async_session_factory() as session:
        yield session


def get_sync_session():
    """
    Get sync session for Celery workers
    """
    return sync_session_factory()
