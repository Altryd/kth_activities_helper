from functools import wraps
import logging

from discord import app_commands, Interaction
from discord.ext import commands

from discord_bot.utils.embeds import get_embed_for_userinfo
from discord_bot.utils.api import APIError, get_user_by_id, get_user_by_username, register_user

logger = logging.getLogger(__name__)


def handle_api_errors(func):
    @wraps(func)
    async def wrapper(self, interaction: Interaction, *args, **kwargs):
        await interaction.response.defer()
        try:
            return await func(self, interaction, *args, **kwargs)
        except APIError as exc:
            await interaction.followup.send(str(exc))
        except Exception:
            logger.exception("Ошибка команды %s", func.__name__)
            await interaction.followup.send("Не удалось выполнить команду. Попробуй позже.")
    return wrapper


class UserInfoCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="userinfo_id", description="Get information about an osu! user by ID")
    @app_commands.describe(userid="The osu! ID of the user")
    @app_commands.rename(userid="user_id")
    @handle_api_errors
    async def userinfo_id(self, interaction: Interaction, userid: int):
        user_data = await get_user_by_id(userid)
        await interaction.followup.send(embed=get_embed_for_userinfo(user_data))

    @app_commands.command(name="userinfo", description="Get information about an osu! user by username")
    @app_commands.describe(username="The osu! username of the user")
    @handle_api_errors
    async def userinfo(self, interaction: Interaction, username: str):
        user_data = await get_user_by_username(username)
        await interaction.followup.send(embed=get_embed_for_userinfo(user_data))

    @app_commands.command(name="register", description="Register in scrims")
    @handle_api_errors
    async def register(self, interaction: Interaction):
        await register_user(str(interaction.user.id))
        await interaction.followup.send("All good :white_check_mark:")


async def setup(bot):
    await bot.add_cog(UserInfoCommands(bot))
