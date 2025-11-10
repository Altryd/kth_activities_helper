import pytest
from backend.database import User, Match, Role
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_match(db_session: AsyncSession):
    """Тест создания матча"""
    player1 = User(
        osu_id=6560308,
        username="Boriska",
        pp=5000.0,
        elo_rating=1500.0,
        role=Role.user
    )
    player2 = User(
        osu_id=11234356,
        username="Meowzarte",
        pp=6000.0,
        elo_rating=1600.0,
        role=Role.user
    )
    db_session.add_all([player1, player2])
    await db_session.flush()  # flush вместо commit для транзакции

    match = Match(
        player1_id=6560308,
        player2_id=11234356,
        player1_score=1000000,
        player2_score=800000,
        winner_id=6560308,
    )
    db_session.add(match)
    await db_session.flush()

    # Проверяем
    db_match = await db_session.get(Match, match.match_id)
    assert db_match.player1_id == 6560308
    assert db_match.player2_id == 11234356
    assert db_match.winner_id == 6560308


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    """Тест создания пользователя"""
    user = User(
        osu_id=1337,
        username="B4riska",
        pp=5000.0,
        elo_rating=1500.0,
        role=Role.user
    )
    db_session.add(user)
    await db_session.flush()

    db_user = await db_session.get(User, 1337)
    assert db_user.username == "B4riska"
    assert db_user.pp == 5000.0
    assert db_user.elo_rating == 1500.0
    assert db_user.role == Role.user
