from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
from backend.database import get_db, User, Role
# Предполагаю, что это ваша функция для получения User по username
from backend.osu_api.get_user import get_user, get_users
from backend.config import OSU_API_ASYNC  # Ваш асинхронный osu_api клиент
from csv import DictReader
from io import StringIO
from pydantic import BaseModel
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.get_logger import logger
import asyncio

admin_router = APIRouter(prefix="/admin", tags=["admin"])


async def require_admin(db: AsyncSession = Depends(get_db), token: HTTPAuthorizationCredentials = Security(HTTPBearer())):  # TODO
    user = await db.execute(select(User).where(User.role == Role.admin)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


class UpdateUserResult(BaseModel):
    status: str  # updated or skipped
    osu_id: int | str | None
    old_pp: float | None
    new_pp: float | None
    username: str | None


# @admin_router.post("/update_all_players_pp")
async def update_all_players_ppold(
        db: AsyncSession = Depends(get_db)) -> List[UpdateUserResult]:
    players_query = select(User)
    all_players = (await db.execute(players_query)).scalars().all()
    batch_size = 35
    # failed_updating = []
    # updated = []
    result = []
    for i in range(0, len(all_players), batch_size):
        players = all_players[i:i + batch_size]
        osu_ids_batch = [player.osu_id for player in players]
        if len(osu_ids_batch) == 0:
            break
        users = await get_users(osu_ids_batch, OSU_API_ASYNC)
        skipped = 0
        for j in range(0, len(osu_ids_batch)):
            player = players[j]
            if osu_ids_batch[j] not in [user.id for user in users]:
                logger.warning(f"unluck: {osu_ids_batch[j]}")
                result.append(UpdateUserResult(status="skipped", osu_id=player.osu_id,
                                               old_pp=player.pp, new_pp=None, username=player.username))
                skipped += 1
            else:
                old_pp = player.pp
                player.pp = users[j - skipped].statistics_rulesets.osu.pp
                # player.updated_at = datetime.datetime.utcnow()
                result.append(UpdateUserResult(status="updated", osu_id=player.osu_id,
                                               old_pp=old_pp, new_pp=player.pp, username=player.username))
    try:
        await db.commit()
    except Exception as e:
        logger.error(e)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Something went wrong")
    return result


@admin_router.post("/update_all_players_pp")
async def update_all_players_pp(
        db: AsyncSession = Depends(get_db)) -> List[UpdateUserResult]:
    result = []
    batch_size = 35
    offset = 0
    api_delay = 1.0  # Delay in seconds between batches to respect API rate limits

    while True:
        players_query = select(User).offset(offset).limit(batch_size)
        players = (await db.execute(players_query)).scalars().all()
        if not players:
            break

        osu_ids_batch = [player.osu_id for player in players]
        users = await get_users(osu_ids_batch, OSU_API_ASYNC) or []
        user_map = {user.id: user for user in users}

        for player in players:
            if player.osu_id not in user_map:
                logger.warning(f"User not found in osu! API: {player.osu_id}")
                result.append(UpdateUserResult(
                    status="skipped",
                    osu_id=player.osu_id,
                    old_pp=player.pp,
                    new_pp=None,
                    username=player.username
                ))
                continue

            old_pp = player.pp
            player.pp = user_map[player.osu_id].statistics_rulesets.osu.pp
            result.append(UpdateUserResult(
                status="updated",
                osu_id=player.osu_id,
                old_pp=old_pp,
                new_pp=player.pp,
                username=player.username
            ))

        offset += batch_size
        await asyncio.sleep(api_delay)  # Respect API rate limits

    try:
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to commit updates: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update players")

    return result


class PreviewChange(BaseModel):
    action: str  # "add" or "update"
    username: str
    osu_id: int | None
    new_elo_rating: float | None
    current_elo_rating: float | None = None  # Если update
    discord_id: str | None = None


@admin_router.post("/preview_csv")
async def preview_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, List[PreviewChange]]:
    """
    Загружает CSV-файл, парсит его и возвращает preview: что добавится/обновится.
    CSV формат: username,rating[,discord_id,osu_id,pp] (опционально discord_id,osu_id,pp).
    Не применяет изменения — только показывает для подтверждения админом.
    """
    content = await file.read()
    content_str = content.decode('utf-8')
    csv_reader = DictReader(StringIO(content_str))

    preview = []
    preprocessing_users = []
    # preprocessing
    for row in csv_reader:
        username = row['username'].strip()
        rating = float(row['rating']) if len(row['rating']) > 1 else None
        discord_id = row.get('discord_id', None)
        osu_id = row.get('osu_id', None)
        # identificator = osu_id if osu_id else username
        # preprocessing_users.append([username, rating, discord_id, osu_id])
        preprocessing_users.append({"username": username, "rating": rating, "discord_id": discord_id,
                                    "osu_id": osu_id})
    osu_ids = []
    for row in preprocessing_users:
        if len(row["osu_id"]) > 0:
            osu_ids.append(int(row['osu_id']))
    osu_ids = [int(row['osu_id'])
               for row in preprocessing_users if len(row['osu_id']) > 0]
    bad_osu_ids = [row['osu_id']
                   for row in preprocessing_users if len(row['osu_id']) == 0]
    bad_osu_usernames = [row['username']
                         for row in preprocessing_users if len(row['osu_id']) == 0]

    if len(bad_osu_ids) > 0:
        raise HTTPException(status_code=404, detail=f"Users with ids: {bad_osu_ids} "
                                                    f"(usernames: {bad_osu_usernames}) are empty / have an error")
    batch_size = 35
    not_found = []
    for i in range(0, len(osu_ids), batch_size):
        osu_ids_batch = osu_ids[i:i + batch_size]
        users = await get_users(osu_ids_batch, OSU_API_ASYNC)
        for osu_id in osu_ids_batch:
            if osu_id not in [user.id for user in users]:
                print(f"unluck: {osu_id}")
                not_found.append(osu_id)
    # not_found = not_found + bad_osu_ids

    if len(not_found) > 0:
        raise HTTPException(
            status_code=404,
            detail=f"Users with ids: {not_found} not found in osu! API")

    csv_reader = DictReader(StringIO(content_str))
    for row in csv_reader:
        username = row['username'].strip()
        rating = float(row['rating']) if len(row['rating']) > 1 else None
        discord_id = row.get('discord_id', None)

        # Получаем osu_id по username через osu! API
        """
        osu_user = await get_user(username, OSU_API_ASYNC)
        if not osu_user or osu_user.statistics.pp < 3000:
            osu_user = await get_user(row.get('osu_id', None), OSU_API_ASYNC)
            if not osu_user:
                raise HTTPException(status_code=404, detail=f"User: {username} not found in osu! API")
        """
        osu_id = row.get('osu_id', None)
        if osu_id is None:
            continue

        # Проверяем наличие в БД
        db_user = await db.get(User, osu_id)
        if db_user:
            # Update: Показываем текущий и новый рейтинг
            preview.append(PreviewChange(
                action="update",
                username=username,
                osu_id=osu_id,
                new_elo_rating=rating,
                current_elo_rating=db_user.elo_rating,
                discord_id=discord_id if discord_id else db_user.discord_id
            ))
        else:
            # Add: Новый игрок
            preview.append(PreviewChange(
                action="add",
                username=username,
                osu_id=osu_id,
                new_elo_rating=rating,
                discord_id=discord_id
            ))

    return {"preview": preview}


class ApplyChangesRequest(BaseModel):
    # Список изменений от preview, возможно подправленный админом
    changes: List[PreviewChange]


@admin_router.post("/apply_csv_changes")
async def apply_csv_changes(
    request: ApplyChangesRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Применяет изменения из preview (возможно, подправленные админом).
    Добавляет/обновляет игроков в БД.
    """
    try:
        for change in request.changes:
            db_user = await db.get(User, change.osu_id)
            if change.action == "add":
                if db_user:
                    raise HTTPException(
                        status_code=400,
                        detail=f"User {change.username} already exists, cannot add")
                new_user = User(
                    osu_id=change.osu_id,
                    username=change.username,
                    elo_rating=change.new_elo_rating,
                    discord_id=change.discord_id,
                    # Другие поля по умолчанию
                )
                db.add(new_user)
            elif change.action == "update":
                if not db_user:
                    raise HTTPException(
                        status_code=404,
                        detail=f"User {change.username} not found for update")
                db_user.elo_rating = change.new_elo_rating
                if change.discord_id:
                    db_user.discord_id = change.discord_id

            await db.commit()
    except BaseException as ex:
        await db.rollback()
        return {"message": f"There is an error: {ex}"}

    return {"message": "Changes applied successfully"}
