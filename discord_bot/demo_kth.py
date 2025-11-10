import discord
from discord.ext import commands
import asyncio
from discord_bot.get_logger import logger
from discord_bot.config import settings

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    logger.info(f'Бот {bot.user} готов и подключён к серверам.')
    try:
        await bot.load_extension("discord_bot.commands.userinfo")
        await bot.load_extension("discord_bot.commands.roulette")
        synced = await bot.tree.sync()
        logger.info(f"Синхронизировано {len(synced)} команд.")
    except Exception as e:
        logger.error(f"Ошибка синхронизации команд: {e}")


bot.run(settings.DISCORD_KTH_TOKEN)
