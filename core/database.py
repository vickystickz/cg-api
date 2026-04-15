from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,          # Keep 10 connections ready
    max_overflow=20,       # Allow 20 more under load
    pool_timeout=30,       # Wait max 30s for a connection
    pool_recycle=1800,     # Refresh connections every 30 min
    pool_pre_ping=True,    # Check if connection is alive before using
    # Set True to see SQL in terminal (noisy but useful for debugging)
    echo=False,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """FastAPI dependency — gives each request its own DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
