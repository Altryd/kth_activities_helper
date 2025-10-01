from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import csv
from io import StringIO, BytesIO
import os
from get_logger import logger
import requests


load_dotenv()
DISCORD_KTH_TOKEN = os.getenv('DISCORD_KTH_TOKEN')  # red_pixel
BOT_API_KEY = os.getenv('BOT_API_KEY')


# Настройка intents
intents = discord.Intents.default()
intents.members = True  # Для доступа к guild.members
intents.message_content = True  # Для чтения сообщений

bot = commands.Bot(command_prefix='!', intents=intents)


def get_auth_headers():
    return {
        "Authorization": f"Bearer {BOT_API_KEY}",
        "Content-Type": "application/json"
    }


@bot.event
async def on_ready():
    logger.info(f'Бот {bot.user} готов и подключён к серверам.')
    try:
        # bot.tree.clear_commands(guild=None)
        # Синхронизация слэш-команд
        synced = await bot.tree.sync()
        logger.info(f"Синхронизировано {len(synced)} команд.")
    except Exception as e:
        logger.error(f"Ошибка синхронизации команд: {e}")


@bot.tree.command(name="userinfo_id", description="Get information about an osu! user by ID")
@app_commands.describe(userid="The osu! ID of the user")
@app_commands.rename(userid='user_id')
async def userinfo_id(interaction: discord.Interaction, userid: int):
    await interaction.response.defer()
    try:
        response = requests.get(f"http://localhost:8101/user/id/{userid}",  # TODO !!
                                headers=get_auth_headers())
        response.raise_for_status()  # Проверяем, успешен ли запрос
        user_data = response.json()

        # Embed для красивого вывода
        embed = discord.Embed(
            title=f"osu! Profile: {user_data['username']}",
            color=discord.Color.blue(),  # Цвет рамки (можно настроить)
            url=f"https://osu.ppy.sh/users/{user_data['osu_id']}"  # Ссылка на профиль osu!
        )

        # аватар
        embed.set_thumbnail(url=f"https://a.ppy.sh/{user_data['osu_id']}")

        # поля с информацией
        embed.add_field(name="Osu! ID", value=user_data['osu_id'], inline=False)
        # embed.add_field(name="Discord ID", value=user_data['discord_id'] or "Not linked", inline=True)
        embed.add_field(name="PP", value=f"{user_data['pp']:.2f}", inline=False)
        embed.add_field(name="Elo Rating", value=f"{user_data['elo_rating']:.2f}", inline=False)
        # embed.add_field(name="Role", value=user_data['role'].capitalize(), inline=True)
        embed.add_field(name="Matches Played", value=len(user_data['matches']), inline=False)

        # Добавляем футер (опционально)
        embed.set_footer(text="4unc Ky")

        # Отправляем Embed
        await interaction.followup.send(embed=embed)

    except requests.exceptions.HTTPError as http_err:
        # Обработка ошибок API (например, 404 - пользователь не найден)
        error_message = response.json().get("detail", "Unknown error")
        await interaction.followup.send(
            # f"Ошибка: {error_message} (Status code: {response.status_code})",
            f"Пользователь не найден :pleading_face:",
            ephemeral=False  # Сообщение видно только пользователю
        )
    except requests.exceptions.RequestException as req_err:
        # Обработка сетевых ошибок
        await interaction.followup.send(
            "Ошибка: Не удалось подключиться к серверу. Попробуйте позже.",
            ephemeral=False
        )
    except KeyError as key_err:
        # Обработка ошибок, если данные от API имеют неожиданный формат
        await interaction.followup.send(
            "Ошибка: Неверный формат данных от сервера.",
            ephemeral=False
        )


@bot.tree.command(name="userinfo", description="Get information about an osu! user by username")
@app_commands.describe(username="The osu! username of the user")
async def userinfo(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    try:
        response = requests.get(f"http://localhost:8101/user/username/{username}",
                                headers=get_auth_headers())
        response.raise_for_status()  # Проверяем, успешен ли запрос
        user_data = response.json()

        # Embed для красивого вывода
        embed = discord.Embed(
            title=f"osu! Profile: {user_data['username']}",
            color=discord.Color.blue(),  # Цвет рамки (можно настроить)
            url=f"https://osu.ppy.sh/users/{user_data['osu_id']}"  # Ссылка на профиль osu!
        )

        # аватар
        embed.set_thumbnail(url=f"https://a.ppy.sh/{user_data['osu_id']}")

        # поля с информацией
        embed.add_field(name="Osu! ID", value=user_data['osu_id'], inline=False)
        # embed.add_field(name="Discord ID", value=user_data['discord_id'] or "Not linked", inline=True)
        embed.add_field(name="PP", value=f"{user_data['pp']:.2f}", inline=False)
        embed.add_field(name="Elo Rating", value=f"{user_data['elo_rating']:.2f}", inline=False)
        # embed.add_field(name="Role", value=user_data['role'].capitalize(), inline=True)
        embed.add_field(name="Matches Played", value=len(user_data['matches']), inline=False)

        # Добавляем футер (опционально)
        embed.set_footer(text="4unc Ky")

        # Отправляем Embed
        await interaction.followup.send(embed=embed)

    except requests.exceptions.HTTPError as http_err:
        # Обработка ошибок API (например, 404 - пользователь не найден)
        error_message = response.json().get("detail", "Unknown error")
        await interaction.followup.send(
            # f"Ошибка: {error_message} (Status code: {response.status_code})",
            f"Пользователь не найден :pleading_face:",
            ephemeral=False  # Сообщение видно только пользователю
        )
    except requests.exceptions.RequestException as req_err:
        # Обработка сетевых ошибок
        await interaction.followup.send(
            "Ошибка: Не удалось подключиться к серверу. Попробуйте позже.",
            ephemeral=False
        )
    except KeyError as key_err:
        # Обработка ошибок, если данные от API имеют неожиданный формат
        await interaction.followup.send(
            "Ошибка: Неверный формат данных от сервера.",
            ephemeral=False
        )

# Запуск бота
# bot.run(os.getenv('DISCORD_BOT_TOKEN'))
bot.run(DISCORD_KTH_TOKEN)  # Твой токен бота
