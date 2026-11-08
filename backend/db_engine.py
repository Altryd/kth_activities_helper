"""Connection pool settings shared by the application and regression tests."""

from sqlalchemy.ext.asyncio import create_async_engine


def create_db_engine(url: str, recycle_seconds: int = 3600):
    return create_async_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=recycle_seconds,
        echo=False,
    )
