import time
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import csv
from io import StringIO, BytesIO
import os
from get_logger import logger
import requests
from config import settings
import random
from datetime import timedelta


# intents
intents = discord.Intents.default()
intents.members = True  # доступ к guild.members
intents.message_content = True  # чтение сообщений

bot = commands.Bot(command_prefix='!', intents=intents)

ROLE_X_ID = 630752620864339989
BASE_MUTE_CHANCE = 50  # базовый порог мута
OVERKILL = 85
CHANCE_INCREASE_PER_STREAK = 5  # +% шанса за каждый streak
BASE_MUTE_MINUTES = 5  # базовое время мута
OVERKILL_MUTE_MULTIPLIER = 2
MINUTES_INCREASE_PER_STREAK = 1  # +минута за каждый streak


def get_auth_headers():
    return {
        "Authorization": f"Bearer {settings.BOT_API_KEY}",
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


def get_embed_for_userinfo(user_data: dict) -> discord.Embed:
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

    active_value = ":red_circle: The player is inactive in scrims"
    if user_data['active']:
        active_value = ":green_circle: The player is active in scrims"
    embed.add_field(name="Activity:", value=active_value, inline=False)

    # Добавляем футер (опционально)
    embed.set_footer(text="4unc Ky")
    return embed


@bot.tree.command(name="userinfo_id", description="Get information about an osu! user by ID")
@app_commands.describe(userid="The osu! ID of the user")
@app_commands.rename(userid='user_id')
async def userinfo_id(interaction: discord.Interaction, userid: int):
    await interaction.response.defer()
    try:
        response = requests.get(f"{settings.SERVER_PROTOCOL}://{settings.SERVER_HOST}:{settings.SERVER_PORT}/user/id/{userid}",  # TODO !!
                                headers=get_auth_headers())
        response.raise_for_status()
        user_data = response.json()

        embed = get_embed_for_userinfo(user_data)  # составляем ембед

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
        response = requests.get(f"{settings.SERVER_PROTOCOL}://{settings.SERVER_HOST}:{settings.SERVER_PORT}/user/username/{username}",
                                headers=get_auth_headers())
        response.raise_for_status()
        user_data = response.json()
        embed = get_embed_for_userinfo(user_data)  # составляем эмбед

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


@bot.tree.command(name="register", description="Register in scrims")
async def userinfo(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        response = requests.post(f"{settings.SERVER_PROTOCOL}://{settings.SERVER_HOST}:{settings.SERVER_PORT}/register",
                                 headers=get_auth_headers(),
                                 json={"discord_id": str(interaction.user.id)})
        response.raise_for_status()
        user_data = response.json()
        # embed = get_embed_for_userinfo(user_data)  # составляем эмбед
        # await interaction.followup.send(f"Your discord_id is {interaction.user.id}")
        await interaction.followup.send("All good :white_check_mark:")  # TODO add more information


    except requests.exceptions.HTTPError as http_err:  # TODO: check with lines
        # Обработка ошибок API (например, 404 - пользователь не найден)
        # error_message = response.json().get("detail", "Unknown error")
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

# Region dodep
history_ids = {}
GIF_FOLDER = "./resources"
ROLE_REMOVED_GIF = os.path.join(GIF_FOLDER, "suigintou-happy.gif")
SURVIVED_GIF = os.path.join(GIF_FOLDER, "suigintou-rozen-maiden-tease.gif")
MUTED_GIF = os.path.join(GIF_FOLDER, "rozen-maiden-suiguintou-muted.gif")
SAMARA_GIF = os.path.join(GIF_FOLDER, "samara-flag-waving.gif")
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:  # Игнорируем ботов
        return

    # упомянута ли роль @X  ?
    if any(role.id == ROLE_X_ID for role in message.role_mentions):
        discord_id = str(message.author.id)
        if discord_id in history_ids and history_ids[discord_id] > 0:
            await message.reply(f"Нононо мистер фиш, ожидайте вынесения приговора")
            return
        streak = 0  # TODO: await get_roulette_streak(discord_id)
        history_ids[discord_id] = 1
        # шанс и время мута
        mute_chance = BASE_MUTE_CHANCE + (CHANCE_INCREASE_PER_STREAK * streak)
        mute_minutes = BASE_MUTE_MINUTES + (MINUTES_INCREASE_PER_STREAK * streak)

        roll = random.randint(1, 100)
        await message.reply(f"Роллю кубик... Если >{mute_chance}, то мут на {mute_minutes} мин.")
        await asyncio.sleep(1)

        role = message.guild.get_role(ROLE_X_ID)
        has_role = True if message.author.get_role(ROLE_X_ID) else False
        if not has_role and role:
            await message.author.add_roles(role)
            await message.reply("Ты пинганул @ X — теперь у тебя тоже эта роль! 😈")
            # return
        # await message.reply(f"Выпало {roll}!")
        if roll == 63:
            string_to_show = f"Выпало {roll}! Ты в му..Погоди погоди! Ты выбил код Самарского региона ГОООООЛ :samara: :skolen: :samara: Живи пока что как свободный (самарский) человек"
            file_to_show = discord.File(SAMARA_GIF, filename="samara.gif")
            await message.reply(string_to_show, file=file_to_show)
        elif roll > mute_chance:
            # мут: используем timeout
            string_to_show = f"Выпало {roll}! Ты в муте на {mute_minutes} минут"
            file_to_show = discord.File(MUTED_GIF, filename="muted.gif")
            if roll == 52:
                string_to_show = f"Выпало {roll}! :zany_face: ПИСЯЯТ ДВААА ыыы :zany_face: Ты в муте на 52..ладно {mute_minutes} минут"
            if roll >= OVERKILL:
                mute_minutes = mute_minutes * OVERKILL_MUTE_MULTIPLIER
                string_to_show = f"Выпало {roll}! :skull: OVERKILL :skull: Ты в муте на {mute_minutes} минут"
            try:
                await message.author.timeout(timedelta(minutes=mute_minutes))
                await message.reply(string_to_show, file=file_to_show)
                # message.author.add_roles(Ro)
                # TODO: await update_roulette_streak(discord_id, 0)  # Reset streak
            except discord.Forbidden:
                await message.reply(f"Выпало {roll}, но блин, у меня нет прав на мут.. :( Так бы я тебя замутил :smiling_imp: ")
        else:
            file = discord.File(SURVIVED_GIF, filename="survived.gif")
            # await message.reply(f"Выжил! Твой streak теперь {streak + 1}. В следующий раз шанс мута выше.")
            await message.reply(f"Выпало {roll}! Тебе повезло..", file=file)
            # TODO: await update_roulette_streak(discord_id, streak + 1)  # Увеличиваем streak
        history_ids[discord_id] = 0

    await bot.process_commands(message)  # Не забываем обрабатывать команды


@bot.tree.command(name="простите-пожалуйста", description="Снять роль @X с позором")
async def prostite_pozhaluysta(interaction: discord.Interaction):
    await interaction.response.defer()

    # роль
    role = interaction.guild.get_role(ROLE_X_ID)
    if not role:
        await interaction.followup.send("Роль @ X не найдена. Сообщи @Boriska")
        return

    # проверяем, есть ли роль у пользователя
    if role not in interaction.user.roles:
        await interaction.followup.send("У тебя и так нет роли @ X. Baka~")
        return

    # снимаем роль
    try:
        await interaction.user.remove_roles(role)
        file = discord.File(ROLE_REMOVED_GIF, filename="role_removed.gif")
        await interaction.followup.send("Роль @ X снята с позором :stuck_out_tongue_winking_eye: ", file=file)
    except discord.Forbidden:
        await interaction.followup.send("У меня нет прав снять роль. Сообщи об этом @Boriska")


# запуск бота
bot.run(settings.DISCORD_KTH_TOKEN)
