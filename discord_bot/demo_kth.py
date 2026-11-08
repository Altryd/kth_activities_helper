import discord
from discord.ext import commands
from discord_bot.get_logger import logger
from discord_bot.config import settings


class KTHBot(commands.Bot):
    async def setup_hook(self):
        for extension in ("userinfo", "roulette", "teams"):
            await self.load_extension(f"discord_bot.commands.{extension}")
        synced = await self.tree.sync()
        logger.info("Синхронизировано %s команд.", len(synced))

    async def on_ready(self):
        logger.info("Бот %s готов и подключён к серверам.", self.user)


def main():
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    bot = KTHBot(command_prefix="!", intents=intents)
    bot.run(settings.DISCORD_KTH_TOKEN)


if __name__ == "__main__":
    main()
