import aiohttp
from discord_bot.config import settings, get_auth_headers


async def get_user_by_id(userid: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{settings.SERVER_PROTOCOL}://{settings.SERVER_HOST}:{settings.SERVER_PORT}/user/id/{userid}",
            headers=get_auth_headers()
        ) as response:
            if response.status != 200:
                error = await response.json()
                raise Exception(error.get("detail", "Unknown error"))
            return await response.json()


async def get_user_by_username(username: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{settings.SERVER_PROTOCOL}://{settings.SERVER_HOST}:{settings.SERVER_PORT}/user/username/{username}",
            headers=get_auth_headers()
        ) as response:
            if response.status != 200:
                error = await response.json()
                raise Exception(error.get("detail", "Unknown error"))
            return await response.json()


async def register_user(discord_id: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{settings.SERVER_PROTOCOL}://{settings.SERVER_HOST}:{settings.SERVER_PORT}/register",
            headers=get_auth_headers(),
            json={"discord_id": discord_id}
        ) as response:
            if response.status != 200:
                error = await response.json()
                raise Exception(error.get("detail", "Unknown error"))
            return await response.json()
