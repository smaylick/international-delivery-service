from sqlalchemy.ext.asyncio import AsyncSession
from .session import AsyncSessionLocal


async def get_async_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
