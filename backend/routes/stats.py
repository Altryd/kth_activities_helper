from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, Union, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.models import UserDTO, UserDTOPublic
from backend.database import get_db, User
# verify_bot_api_key
from backend.utility.verification import verify_jwt, optional_auth, verify_auth
import jwt

router = APIRouter()


@router.get("/get_roulette_stats")
async def get_roulette_stats(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
) -> List[UserDTOPublic]:
    # Вычисляем win_rate_percent через SQLAlchemy
    win_rate = func.round(
        (User.roulette_wins * 100.0 / func.nullif(User.roulette_rolls, 0)), 2
    ).label("roulette_winrate")

    query = (
        select(
            User.osu_id,
            User.username,
            User.pp,
            User.elo_rating,
            User.active,
            User.roulette_rolls,
            User.roulette_wins,
            User.roulette_achievements,
            User.roulette_streak_current,
            win_rate
        )
        .where(User.roulette_rolls > 0)
        .order_by(User.roulette_rolls.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(query)
    rows = result.all()
    # Преобразуем в DTO
    return [
        UserDTOPublic(
            osu_id=row.osu_id,
            username=row.username,
            pp=row.pp,
            elo_rating=row.elo_rating,
            matches=None,  # не нужно для рулетки
            active=row.active,
            roulette_rolls=row.roulette_rolls,
            roulette_wins=row.roulette_wins,
            roulette_achievements=row.roulette_achievements,
            roulette_streak_current=row.roulette_streak_current,
            roulette_winrate=row.roulette_winrate
        )
        for row in rows
    ]
