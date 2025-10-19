from functools import wraps

from discord import app_commands, Interaction
from discord.ext import commands
from discord_bot.utils.embeds import get_embed_for_userinfo
from discord_bot.utils.api import get_user_by_id, get_user_by_username, register_user


def handle_api_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        interaction = next((arg for arg in args if isinstance(arg, Interaction)), None)
        await interaction.response.defer()
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            await interaction.followup.send(f"Ошибка: {str(e)} :pleading_face:", ephemeral=False)
    return wrapper


class UserInfoCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="userinfo_id", description="Get information about an osu! user by ID")
    @app_commands.describe(userid="The osu! ID of the user")
    @app_commands.rename(userid='user_id')
    @handle_api_errors
    async def userinfo_id(self, interaction: Interaction, userid: int):
        await interaction.response.defer()
        try:
            user_data = await get_user_by_id(userid)
            embed = get_embed_for_userinfo(user_data)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"Ошибка: {str(e)} :pleading_face:", ephemeral=False)

    @app_commands.command(name="userinfo", description="Get information about an osu! user by username")
    @app_commands.describe(username="The osu! username of the user")
    @handle_api_errors
    async def userinfo(self, interaction: Interaction, username: str):
        await interaction.response.defer()
        try:
            user_data = await get_user_by_username(username)
            embed = get_embed_for_userinfo(user_data)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"Ошибка: {str(e)} :pleading_face:", ephemeral=False)

    @app_commands.command(name="register", description="Register in scrims")
    @handle_api_errors
    async def register(self, interaction: Interaction):
        await interaction.response.defer()
        try:
            user_data = await register_user(str(interaction.user.id))
            await interaction.followup.send("All good :white_check_mark:")
        except Exception as e:
            await interaction.followup.send(f"Ошибка: {str(e)} :pleading_face:", ephemeral=False)


async def setup(bot):
    await bot.add_cog(UserInfoCommands(bot))