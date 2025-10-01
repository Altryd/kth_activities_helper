from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, Union
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.models import UserDTO, UserDTOPublic
from backend.database import get_db, User
from backend.utility.verification import verify_jwt, optional_auth, verify_auth  # verify_bot_api_key
import jwt

router = APIRouter()


# Модель для тела запроса
class RegisterRequest(BaseModel):
    discord_id: Optional[str] = None  # Discord ID для бота, опционально


# Единый роут для регистрации
@router.post("/register")
async def register_user(
    request: RegisterRequest,
    auth_info: Optional[dict] = Depends(verify_auth),
    db: AsyncSession = Depends(get_db)
):
    # Если посылается с фронтенда - тогда нужно в JWT проверять. Если же с бота - тогда просто по апи ключу..
    user_id = None
    if not auth_info:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    if auth_info["type"] == "bot":
        user_id = request.discord_id
        player_query = (
            select(User)
            .where(User.discord_id == user_id)
            .options(
                selectinload(User.matches_as_player1),
                selectinload(User.matches_as_player2)
            )
        )
    elif auth_info["type"] == "user":
        pass  # TODO JWT
        player_query = (
            select(User)
            .where(User.osu_id == user_id)
            .options(
                selectinload(User.matches_as_player1),
                selectinload(User.matches_as_player2)
            )
        )
    else:
        raise HTTPException(status_code=401, detail="Invalid authentication")


    player = (await db.execute(player_query)).scalars().first()
    if not player:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        player.active = True
        await db.commit()
    except BaseException as ex:    # TODO: add more exceptions
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error")

    # Здесь логика регистрации в базе данных
    # Например, сохраняем user_id (или discord_id) в таблицу registered_events
    return {"message": f"User {user_id} registered successfully"}


@router.get("/user/id/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)) -> UserDTO:
    player_query = (
        select(User)
        .where(User.osu_id == user_id)
        .options(
            selectinload(User.matches_as_player1),
            selectinload(User.matches_as_player2)
        )
    )
    player = (await db.execute(player_query)).scalars().first()
    if not player:
        raise HTTPException(status_code=404, detail="User not found")
    userDTO = UserDTO.from_orm(player)
    userDTO.matches = player.matches
    return userDTO


@router.get("/user/username/{username}")  # , dependencies=[Depends(verify_bot_api_key)])
async def get_user_by_username(username: str, auth_info: Optional[dict] = Depends(optional_auth),
                               db: AsyncSession = Depends(get_db)) -> Union[UserDTO, UserDTOPublic]:
    # test = verify_bot_api_key(authorization)
    # print(test)
    player_query = (
        select(User)
        .where(func.lower(User.username) == username.lower())
        .options(
            selectinload(User.matches_as_player1),
            selectinload(User.matches_as_player2)
        )
    )
    player = (await db.execute(player_query)).scalars().first()
    if not player:
        raise HTTPException(status_code=404, detail="User not found")
        # Определяем тип DTO в зависимости от авторизации
    dto_class = UserDTO if auth_info else UserDTOPublic
    user_dto = dto_class.from_orm(player)
    user_dto.matches = player.matches

    return user_dto
