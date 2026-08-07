"""
Professional AI - Database Engine & Session Management
Async SQLAlchemy engine with PostgreSQL connection pooling, SSL, retry logic,
and automatic schema migration on startup.
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.config import settings
from loguru import logger
import asyncio


def _create_engine():
    """Create async engine with PostgreSQL connection pooling and SSL."""
    engine_kwargs = {
        "echo": settings.DEBUG,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "pool_size": 20,
        "max_overflow": 10,
        "pool_timeout": 30,
    }

    if "postgresql" in settings.DATABASE_URL or "postgres" in settings.DATABASE_URL:
        import ssl

        connect_args = {
            "timeout": 30,
            "server_settings": {
                "application_name": "professional-ai-backend",
                "jit": "off",
            },
        }

        # Only enable SSL when explicitly required/verified
        if settings.DB_SSL_MODE in ("require", "verify-ca", "verify-full"):
            ssl_context = ssl.create_default_context()
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            if settings.DB_SSL_MODE == "verify-full":
                ssl_context.verify_mode = ssl.CERT_REQUIRED
                ssl_context.check_hostname = True
            elif settings.DB_SSL_MODE == "verify-ca":
                ssl_context.verify_mode = ssl.CERT_REQUIRED
                ssl_context.check_hostname = False
            else:
                # "require" — encrypt but don't verify
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            connect_args["ssl"] = ssl_context

        engine_kwargs.update({
            "connect_args": connect_args,
        })
    else:
        # Fallback for non-PostgreSQL (should not happen in production)
        engine_kwargs.update({
            "connect_args": {"timeout": 30},
        })

    return create_async_engine(settings.DATABASE_URL, **engine_kwargs)


# Lazy engine initialization with retry
_engine = None
_async_session_factory = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = _create_engine()
    return _engine


def _get_session_factory():
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injector for database sessions."""
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            await session.close()


async def init_db(max_retries: int = 5, retry_delay: float = 1.0):
    """
    Initialize database - run PostgreSQL migrations automatically on startup.
    Creates all tables, functions, triggers, and RLS policies if missing.
    """
    from app.migrations import run_migrations, check_core_tables_exist

    engine = _get_engine()

    for attempt in range(1, max_retries + 1):
        try:
            # Run the full schema.sql migration (idempotent)
            database_url = settings.DATABASE_URL
            success = await run_migrations(database_url)
            if success:
                logger.info("Auto-migration completed successfully")
            else:
                logger.error("Auto-migration failed")
            
            # Verify core tables exist
            tables_ok = await check_core_tables_exist(database_url)
            if not tables_ok:
                logger.error("Core tables missing after migration — check schema.sql")
            return
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"Database initialization failed after {max_retries} attempts: {e}")
                raise
            logger.warning(f"Database initialization attempt {attempt} failed: {e}. Retrying in {retry_delay}s...")
            await asyncio.sleep(retry_delay * attempt)


async def close_db():
    """Close database connections gracefully."""
    global _engine, _async_session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
        logger.info("Database connections closed")


async def check_db_connection() -> bool:
    """Check if database is reachable."""
    try:
        engine = _get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False