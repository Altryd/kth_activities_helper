import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.database import Base
from backend.config import settings

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    """Создаем тестовый движок один раз на всю сессию"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,  # Отключаем логи для чистоты вывода
        connect_args={"check_same_thread": False}
    )
    return engine


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine):
    """Создаем чистую сессию для каждого теста с rollback"""

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        # начинаем транзакцию
        async with session.begin():
            yield session
            # после теста откатываем все изменения
            await session.rollback()

    # очищаем таблицы после теста
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def cleanup_engine(test_engine):
    """Очищаем пул соединений после каждого теста"""
    yield
    await test_engine.dispose()
