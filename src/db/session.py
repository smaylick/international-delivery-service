from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.core.settings import settings

engine: AsyncEngine = create_async_engine(
    settings.db_url,
    echo=True,
    future=True,
)

AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
)

_sync_engine = create_engine(
    settings.sync_db_url,
    pool_pre_ping=True,
)


def get_sync_session() -> Session:
    return Session(_sync_engine)
