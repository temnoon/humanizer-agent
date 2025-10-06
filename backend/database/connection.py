"""Database connection management for PostgreSQL + pgvector."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from config import settings
from models.db_models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and lifecycle."""

    def __init__(self):
        """Initialize database manager."""
        self.engine = None
        self.async_session_maker = None
        self._initialized = False

    async def initialize(self):
        """Initialize database engine and session maker."""
        if self._initialized:
            return

        logger.info(f"Initializing database connection: {settings.database_url}")

        # Create async engine
        self.engine = create_async_engine(
            settings.database_url,
            echo=False,  # Set to True for SQL query logging
            pool_pre_ping=True,
            poolclass=NullPool if "sqlite" in settings.database_url else None,
        )

        # Create session maker
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        self._initialized = True
        logger.info("Database connection initialized")

    async def create_tables(self):
        """
        Create all tables if they don't exist.

        DEPRECATED: For development/testing only.
        In production, use Alembic migrations instead:
            alembic upgrade head

        This method bypasses migration tracking and should only be used
        for quick local testing. All schema changes should go through
        Alembic to maintain version control and rollback capability.
        """
        if not self._initialized:
            await self.initialize()

        logger.warning(
            "Using create_all() - this bypasses Alembic migrations. "
            "For production, use: alembic upgrade head"
        )

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified (via create_all - not Alembic)")

    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")
            self._initialized = False

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session context manager."""
        if not self._initialized:
            await self.initialize()

        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Global database manager instance
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session.

    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with db_manager.session() as session:
        yield session


async def init_db():
    """Initialize database - call at startup."""
    await db_manager.initialize()
    await db_manager.create_tables()


async def close_db():
    """Close database - call at shutdown."""
    await db_manager.close()
