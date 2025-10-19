# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from backend.config import settings
from backend.database import init_db, get_db
from backend.database import User, Match, Role  # ,  MatchStatus
from backend.osu_api.get_user import get_users
from backend.models import UserDTO, MatchResult
from contextlib import asynccontextmanager
from backend.routes import pairs, admin, user


# @app.on_event("startup")
# async def startup_event():
#    await init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)


async def get_osu_api():
    return settings.OSU_API_ASYNC


# Эндпоинт для получения пользователей
@app.post("/users")
async def fetch_users(ids: List[int], osu_api=Depends(
        get_osu_api), db: AsyncSession = Depends(get_db)):
    users = await get_users(ids, osu_api, db)
    if not users:
        raise HTTPException(status_code=404, detail="No users found")

    return [UserDTO(osu_id=user.id, discord_id=None, username=user.username, pp=user.statistics_rulesets.osu.pp,
                    elo_rating=user.statistics_rulesets.osu.pp * 10, role=Role.user) for user in users]


# Эндпоинт для записи матча
@app.post("/match")
async def record_match(result: MatchResult,
                       db: AsyncSession = Depends(get_db)):
    if result.player1_id == result.player2_id:
        raise HTTPException(
            status_code=400,
            detail="Players must be different")

    # Проверяем существование игроков
    player1 = await db.get(User, result.player1_id)
    player2 = await db.get(User, result.player2_id)
    if not player1 or not player2:
        raise HTTPException(status_code=404,
                            detail="One or both players not found")

    # Расчёт Elo
    winner_id = result.player1_id if result.player1_score > result.player2_score else result.player2_id
    loser_id = result.player2_id if result.player1_score > result.player2_score else result.player1_id
    winner = player1 if winner_id == player1.osu_id else player2
    loser = player2 if loser_id == player2.osu_id else player1

    expected_winner = 1 / (1 + 10 ** ((loser.rating - winner.rating) / 400))
    expected_loser = 1 / (1 + 10 ** ((winner.rating - loser.rating) / 400))
    new_winner_elo = winner.rating + 32 * (1 - expected_winner)
    new_loser_elo = loser.rating + 32 * (0 - expected_loser)

    # Обновляем рейтинги
    winner.rating = new_winner_elo
    loser.rating = new_loser_elo

    # Сохраняем матч
    match = Match(
        player1_id=result.player1_id,
        player2_id=result.player2_id,
        player1_score=result.player1_score,
        player2_score=result.player2_score,
        winner_id=winner_id,
        # status=MatchStatus.completed
    )
    db.add(match)
    await db.commit()

    return {
        "match_id": match.match_id,
        "winner_id": winner_id,
        "new_winner_elo": round(new_winner_elo),
        "loser_id": loser_id,
        "new_loser_elo": round(new_loser_elo)
    }


if __name__ == "__main__":
    import uvicorn
    app.include_router(pairs.router)
    app.include_router(admin.admin_router)
    app.include_router(user.router)
    uvicorn.run(app, host=settings.SERVER_HOST, port=settings.SERVER_PORT)
