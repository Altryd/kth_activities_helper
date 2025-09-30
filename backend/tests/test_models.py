# tests/test_models.py
import pytest
from backend.database import User, Match, Role  # , MatchStatus
from backend.database import async_session, reset_db, get_db, async_engine
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(scope="function")
async def db():
    await reset_db()  # Очищаем базу перед каждым тестом
    async with async_session() as session:
        yield session
        await session.rollback()
        await session.close()
    await async_engine.dispose()  # Очищаем пул соединений после теста


@pytest.mark.asyncio
async def test_create_match(db: AsyncSession):
    player1 = User(osu_id=6560308, username="Boriska", pp=5000.0, elo_rating=1500.0, role=Role.user)
    player2 = User(osu_id=11234356, username="Meowzarte", pp=6000.0, elo_rating=1600.0)
    db.add_all([player1, player2])
    await db.commit()

    match = Match(
        player1_id=6560308,
        player2_id=11234356,
        player1_score=1000000,
        player2_score=800000,
        winner_id=6560308,
        # status=MatchStatus.completed
    )
    db.add(match)
    await db.commit()

    db_match = await db.get(Match, match.match_id)
    assert db_match.player1_id == 6560308
    assert db_match.player2_id == 11234356
    assert db_match.winner_id == 6560308
    # assert db_match.status == MatchStatus.completed


@pytest.mark.asyncio
async def test_create_user(db: AsyncSession):
    user = User(osu_id=1337, username="B4riska", pp=5000.0, elo_rating=1500.0, role=Role.user)
    db.add(user)
    await db.commit()

    db_user = await db.get(User, 1337)
    assert db_user.username == "B4riska"
    assert db_user.pp == 5000.0
    assert db_user.elo_rating == 1500.0
    assert db_user.role == Role.user