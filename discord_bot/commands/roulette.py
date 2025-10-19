from typing import Tuple

import discord
from discord import app_commands, Interaction, File
from discord.ext import commands
from discord_bot.config import settings
import random
from datetime import timedelta
import os


class RouletteCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.history_ids = {}
        self.ROLE_X_ID = settings.ROLE_X_ID
        self.BOTS_COMMAND_ID = settings.BOTS_COMMAND_ID
        self.GIF_FOLDER = settings.GIF_FOLDER
        self.ROLE_REMOVED_GIF = os.path.join(
            self.GIF_FOLDER, "suigintou-happy.gif")
        self.SURVIVED_GIF = os.path.join(
            self.GIF_FOLDER, "suigintou-rozen-maiden-tease.gif")
        self.MUTED_GIF = os.path.join(
            self.GIF_FOLDER, "rozen-maiden-suiguintou-muted.gif")
        self.SAMARA_GIF = os.path.join(
            self.GIF_FOLDER, "samara-flag-waving.gif")
        self.DODEP_GIF = os.path.join(self.GIF_FOLDER, "dodep.gif")
        self.samara_emoji = "<:samara:1416124739981938709>"
        self.skolen_emoji = "<:skolen:541635738182090767>"

    async def get_timeout_and_message(self, roll: int, mute_chance: int, mute_minutes: int) -> (
            tuple[str, File, None] | tuple[str, File, int]):
        if roll == 63:
            return (
                f"Выпало {roll}! Ты в му..Погоди погоди! Ты выбил код Самарского региона ГОООООЛ "
                f"{self.samara_emoji} {self.skolen_emoji} {self.samara_emoji} Живи пока что как свободный (самарский) человек",
                discord.File(self.SAMARA_GIF, filename="samara.gif"),
                None
            )
        elif roll > mute_chance:
            if roll == 52:
                message = f"Выпало {roll}! :zany_face: ПИСЯЯТ ДВААА ыыы :zany_face: Ты в муте на {mute_minutes} минут"
            elif roll >= settings.OVERKILL:
                mute_minutes *= settings.OVERKILL_MUTE_MULTIPLIER
                message = f"Выпало {roll}! :skull: OVERKILL :skull: Ты в муте на {mute_minutes} минут"
            else:
                message = f"Выпало {roll}! Ты в муте на {mute_minutes} минут"
            return message, discord.File(
                self.MUTED_GIF, filename="muted.gif"), mute_minutes
        else:
            return (
                f"Выпало {roll}! Тебе повезло..",
                discord.File(self.SURVIVED_GIF, filename="survived.gif"),
                None
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if any(role.id == self.ROLE_X_ID for role in message.role_mentions):
            if message.channel.id != self.BOTS_COMMAND_ID:
                bots_channel = self.bot.get_channel(self.BOTS_COMMAND_ID)
                if bots_channel:
                    file_to_show = discord.File(
                        self.DODEP_GIF, filename="dodep.gif")
                    await bots_channel.send(
                        f"Ты {message.author.mention} попытался пингануть @X в {message.channel.mention}! "
                        f"\nДелай это здесь, чтобы сыграть в ~~додеп~~-рулетку! 🎰 ", file=file_to_show
                    )
                return
            discord_id = str(message.author.id)
            if discord_id in self.history_ids and self.history_ids[discord_id] > 0:
                await message.reply(f"Нононо мистер фиш, ожидайте вынесения приговора")
                return
            streak = 0  # TODO: await get_roulette_streak(discord_id)
            self.history_ids[discord_id] = 1
            mute_chance = settings.BASE_MUTE_CHANCE + \
                (settings.CHANCE_INCREASE_PER_STREAK * streak)
            mute_minutes = settings.BASE_MUTE_MINUTES + \
                (settings.MINUTES_INCREASE_PER_STREAK * streak)

            await message.reply(f"Роллю кубик... Если >{mute_chance}, то мут на {mute_minutes} мин.")
            role = message.guild.get_role(self.ROLE_X_ID)
            has_role = True if message.author.get_role(
                self.ROLE_X_ID) else False
            if not has_role and role:
                await message.author.add_roles(role)
                await message.reply("Ты пинганул @ X — теперь у тебя тоже эта роль! 😈")
            roll = random.randint(1, 100)
            string_to_show, file, mute_for = await self.get_timeout_and_message(roll, mute_chance, mute_minutes)
            if mute_for and mute_for > 0:
                try:
                    await message.author.timeout(timedelta(minutes=mute_for))
                except discord.Forbidden:
                    string_to_show = f"Выпало {roll}, но блин, у меня нет прав на мут.. :( Так бы я тебя замутил :smiling_imp: "
                    file = None
            await message.reply(string_to_show, file=file)
            self.history_ids[discord_id] = 0

    @app_commands.command(name="простите-пожалуйста",
                          description="Снять роль @X с позором")
    async def prostite_pozhaluysta(self, interaction: Interaction):
        await interaction.response.defer()
        role = interaction.guild.get_role(self.ROLE_X_ID)
        if not role:
            await interaction.followup.send("Роль @ X не найдена. Сообщи @Boriska")
            return
        if role not in interaction.user.roles:
            await interaction.followup.send("У тебя и так нет роли @ X. Baka~")
            return
        try:
            await interaction.user.remove_roles(role)
            file = discord.File(
                self.ROLE_REMOVED_GIF,
                filename="role_removed.gif")
            await interaction.followup.send("Роль @ X снята с позором :stuck_out_tongue_winking_eye: ", file=file)
        except discord.Forbidden:
            await interaction.followup.send("У меня нет прав снять роль. Сообщи об этом @Boriska")


async def setup(bot):
    await bot.add_cog(RouletteCommands(bot))
