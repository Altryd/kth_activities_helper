import asyncio
from urllib.parse import quote

import aiohttp

from discord_bot.config import settings, get_auth_headers


class APIError(Exception):
    """A user-facing error; do not expose backend tracebacks or credentials."""


async def request_api(method: str, path: str, **kwargs):
    url = f"{settings.SERVER_PROTOCOL}://{settings.SERVER_HOST}:{settings.SERVER_PORT}{path}"
    timeout = aiohttp.ClientTimeout(total=settings.API_TIMEOUT_SECONDS)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.request(method, url, headers=get_auth_headers(), **kwargs) as response:
                if response.status >= 500:
                    raise APIError("Сервис временно недоступен. Попробуй позже.")
                try:
                    data = await response.json()
                except (ValueError, aiohttp.ContentTypeError) as exc:
                    raise APIError("Сервис вернул некорректный ответ.") from exc
                if not 200 <= response.status < 300:
                    detail = data.get("detail") if isinstance(data, dict) else None
                    raise APIError(detail if isinstance(detail, str) else f"Ошибка сервиса: HTTP {response.status}.")
                return data
    except (asyncio.TimeoutError, aiohttp.ClientError) as exc:
        raise APIError("Не удалось связаться с сервисом. Попробуй позже.") from exc


async def get_user_by_id(userid: int):
    return await request_api("GET", f"/user/id/{userid}")


async def get_user_by_username(username: str):
    return await request_api("GET", f"/user/username/{quote(username, safe='')}")


async def register_user(discord_id: str):
    return await request_api("POST", "/register", json={"discord_id": discord_id})


async def get_roulette_stats(discord_id: str) -> dict:
    return await request_api("GET", f"/user/{discord_id}/roulette_stats")


async def update_roulette_stats(discord_id: str, roll: int, won: bool, streak: int, achievements: list[str]):
    # Never retry this POST automatically: a lost response may follow a committed roll.
    return await request_api("POST", f"/user/{discord_id}/update_roulette", json={
        "roll": roll, "won": won, "streak": streak, "achievements": achievements,
    })


async def get_roulette_leaderboard(limit: int = 20, offset: int = 0) -> list[dict]:
    return await request_api("GET", "/get_roulette_stats", params={"limit": limit, "offset": offset})
