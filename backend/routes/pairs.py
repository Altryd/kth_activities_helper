from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Tuple

from sqlalchemy.orm import selectinload

from backend.database import User, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.get_logger import logger
from datetime import datetime, timedelta

router = APIRouter()


class CreatePairsRequest(BaseModel):
    # Временно используемые игроки (ники)
    temporary_used_players: Optional[List[str]] = []
    # Корректировки от админа: [[player1_nick, player2_nick], ...
    pairs_correction: Optional[List[List[str]]] = []


@router.post("/create_pairs")
async def create_pairs(request: CreatePairsRequest,
                       db: AsyncSession = Depends(get_db)):
    """
    Создание 1v1 пар игроков на основе Elo-рейтинга.
    Учитывает корректировки админа, временно используемых игроков и предыдущие матчи.
    """
    temporary_used_players = set(request.temporary_used_players)
    pairs_correction_list = request.pairs_correction
    used_players = set(temporary_used_players)
    pairs: List[Tuple[User, User]] = []
    unused = []

    # Получаем активных игроков, отсортированных по elo_rating desc
    players_query = (
        select(User)
        .where(User.active.is_(True))
        .options(
            selectinload(User.matches_as_player1),
            selectinload(User.matches_as_player2)
        )
        .order_by(desc(User.elo_rating))
    )
    players = (await db.execute(players_query)).scalars().all()

    # Обработка корректировок от админа
    for pair in pairs_correction_list:
        if len(pair) != 2:
            continue
        first_nick, second_nick = pair[0].lower(), pair[1].lower()
        first_player = next(
            (p for p in players if p.username.lower() == first_nick), None)
        second_player = next(
            (p for p in players if p.username.lower() == second_nick), None)
        if not first_player:
            raise HTTPException(
                status_code=404,
                detail=f"Player with username {pair[0]} not found")
        if not second_player:
            raise HTTPException(
                status_code=404,
                detail=f"Player with username {pair[1]} not found")
        if first_player.osu_id == second_player.osu_id:
            raise HTTPException(
                status_code=400,
                detail="Players must be different")
        used_players.add(first_player.username)
        used_players.add(second_player.username)
        pairs.append((first_player, second_player))
        logger.info(
            f"Admin correction: {first_player.username} vs {second_player.username}")

    # Сет всех игроков для расчёта неиспользованных
    all_players_set = {p.username for p in players}

    # Подбор оставшихся пар
    overpowered_players = []
    # Интервал для проверки предыдущих матчей
    one_year_ago = datetime.utcnow() - timedelta(days=365)
    for player in players:
        if player.username in used_players:
            continue
        opponent_found = False
        for opponent in players:
            if opponent.username in used_players or opponent.osu_id == player.osu_id:
                continue
            rating_diff = abs(player.elo_rating - opponent.elo_rating)
            if rating_diff >= 300:
                continue  # Слишком большая разница, ищем другого TODO maybe break ?

            # Проверка предыдущих матчей (с учётом интервала 1 год)
            skip = False
            for match in player.matches:
                if match.match_date < one_year_ago:
                    continue  # Матч старше 1 года — ok
                if match.player1_id == opponent.osu_id or match.player2_id == opponent.osu_id:
                    skip = True
                    break
            if skip:
                continue

            pairs.append((player, opponent))
            used_players.add(player.username)
            used_players.add(opponent.username)
            opponent_found = True
            logger.info(
                f"Matched: {player.username} ({player.elo_rating}) vs {opponent.username} ({opponent.elo_rating})")
            break

        if not opponent_found:
            if any(abs(player.elo_rating - p.elo_rating) < 300 for p in players if
                   p.username not in used_players and p.osu_id != player.osu_id):  # TODO wtf ?
                # Не найден из-за нехватки пары
                unused.append(
                    f"Неиспользованный игрок (нехватка пары): {player.username}, elo_rating {player.elo_rating}")
            else:
                # Overpowered
                overpowered_players.append(
                    (player.username, player.elo_rating))
                used_players.add(player.username)
                unused.append(
                    f"Не найден подходящий соперник (skill issue): {player.username}, elo_rating {player.elo_rating}")

    # Неиспользованные игроки (остальные причины)
    unused_players = all_players_set - used_players
    for unused_nick in unused_players:
        player = next((p for p in players if p.username == unused_nick), None)
        if player:
            unused.append(
                f"Неиспользованный игрок (другие причины): {unused_nick}, elo_rating {player.elo_rating}")

    # Формирование ответа
    pairs_nickname = [(f"{pair[0].username} ({pair[0].elo_rating}) (pp: {pair[0].pp}) vs "
                       f"{pair[1].username} ({pair[1].elo_rating}) (pp: {pair[1].pp})")
                      for pair in pairs]
    pairs_discord = [f"<@{pair[0].discord_id}> vs <@{pair[1].discord_id}>" for pair in pairs if
                     pair[0].discord_id and pair[1].discord_id]
    pairs_raw = [f"{pair[0].username},{pair[1].username}" for pair in pairs]

    return {
        "pairs_nickname": pairs_nickname,
        "pairs_discord": pairs_discord,
        "unused": unused,
        "pairs_raw": pairs_raw
    }
