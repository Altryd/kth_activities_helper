"""Team roles, private channels and read-only archives; no backend dependency."""

import io
import logging
import re

import discord
from discord import app_commands
from discord.ext import commands

from discord_bot.config import settings

logger = logging.getLogger(__name__)


class TeamError(app_commands.AppCommandError):
    pass


def admin_role(member):
    for role in member.roles:
        if settings.TEAM_ADMIN_ROLE_ID is not None:
            if role.id == settings.TEAM_ADMIN_ROLE_ID:
                return role
        elif role.name == settings.TEAM_ADMIN_ROLE_NAME:
            return role
    return None


def role_can_view(channel, role):
    return channel.overwrites_for(role).view_channel is True


def has_team_brackets(name):
    return re.search(r"\[[^\[\]]*\]", name) is not None


def is_team_role(role, staff_role=None):
    return (role is not None and has_team_brackets(role.name)
            and not role.is_default() and not role.managed
            and not role.permissions.administrator
            and (staff_role is None or role.id != staff_role.id))


async def resolve_category(guild, selected, default_id, label):
    channel_id = selected.id if selected is not None else default_id
    if selected is not None and selected.guild.id != guild.id:
        raise TeamError(f"{label}: выбери категорию этого сервера.")
    try:
        category = await guild.fetch_channel(channel_id)
    except (discord.NotFound, discord.Forbidden, discord.InvalidData) as exc:
        raise TeamError(f"{label}: категория {channel_id} недоступна. Выбери категорию в параметрах команды.") from exc
    if not isinstance(category, discord.CategoryChannel):
        raise TeamError(f"{label}: нужен именно канал-категория.")
    return category


async def helper_bot_members(guild):
    members = []
    for bot_id in dict.fromkeys(settings.TEAM_HELPER_BOT_IDS):
        try:
            member = await guild.fetch_member(bot_id)
        except discord.HTTPException as exc:
            raise TeamError(f"Не удалось найти osu!-бота {bot_id} на сервере. Проверь TEAM_HELPER_BOT_IDS.") from exc
        if not member.bot:
            raise TeamError(f"Участник {bot_id} не бот. Проверь TEAM_HELPER_BOT_IDS.")
        members.append(member)
    return members


def voice_channels_for_role(channels, role, category_id=None):
    if not is_team_role(role):
        return []
    if category_id is None:
        category_id = settings.TEAM_VOICE_CATEGORY_ID
    return [channel for channel in channels
            if isinstance(channel, discord.VoiceChannel)
            and channel.category_id == category_id
            and role_can_view(channel, role)]


async def fetch_voice_candidates(guild, role, category_id):
    # The bulk fetch_channels() fails if ANY guild channel has an unknown type.
    # Discover known voice IDs from the gateway cache; verify each one over REST.
    candidates = voice_channels_for_role(guild.voice_channels, role, category_id)
    verified = []
    for candidate in candidates:
        try:
            channel = await guild.fetch_channel(candidate.id)
        except (discord.NotFound, discord.Forbidden, discord.InvalidData):
            logger.warning("Пропущен недоступный или неподдерживаемый голосовой канал %s", candidate.id)
            continue
        if voice_channels_for_role([channel], role, category_id):
            verified.append(channel)
    return verified


async def create_team_resources(guild, name, members, text_category, voice_category, staff_role, reason, *, helper_bots=()):
    created = []
    try:
        role = await guild.create_role(name=name, colour=discord.Colour.random(), reason=reason)
        created.append(role)
        for member in members:
            await member.add_roles(role, reason=reason)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            role: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True),
            staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True,
                                                 manage_channels=True, manage_roles=True),
        }
        text_overwrites = dict(overwrites)
        for helper in helper_bots:
            if helper not in text_overwrites:
                text_overwrites[helper] = discord.PermissionOverwrite(
                    view_channel=True, read_message_history=True, send_messages=True,
                    embed_links=True, attach_files=True,
                )
        text = await guild.create_text_channel(name, category=text_category, overwrites=text_overwrites, reason=reason)
        created.append(text)
        voice = await guild.create_voice_channel(name, category=voice_category, overwrites=overwrites, reason=reason)
        created.append(voice)
        return role, text, voice
    except Exception as exc:
        remaining = []
        for resource in reversed(created):
            try:
                await resource.delete(reason="Откат незавершённого создания команды")
            except discord.NotFound:
                pass
            except Exception:
                logger.exception("Не удалось удалить ресурс %s при откате", resource.id)
                remaining.append(str(resource.id))
        message = "Не удалось создать команду. Созданные ресурсы удалены."
        if remaining:
            message = "Не удалось создать команду. Проверь оставшиеся ресурсы: " + ", ".join(remaining)
        raise TeamError(message) from exc


def read_only(overwrite, *, preserve_access=False):
    if preserve_access:
        overwrite.view_channel = True
        overwrite.read_message_history = True
    overwrite.send_messages = False
    overwrite.send_tts_messages = False
    overwrite.send_messages_in_threads = False
    overwrite.create_public_threads = False
    overwrite.create_private_threads = False
    return overwrite


async def archive_permissions(channel, role, members, reason):
    """Preserve unrelated overwrites and attempt rollback on a partial failure."""
    if not is_team_role(role):
        raise TeamError("Архивировать можно только командную роль с квадратными скобками [ ], например [KTH] Team.")
    changed = []
    original = channel.overwrites
    try:
        for target in [role, *members]:
            previous = original.get(target)
            overwrite = read_only(channel.overwrites_for(target), preserve_access=target is not role)
            # Include a failed request too: it may have reached Discord before a lost response.
            changed.append((target, previous))
            await channel.set_permissions(target, overwrite=overwrite, reason=reason)
    except Exception as exc:
        failed = []
        for target, previous in reversed(changed):
            try:
                await channel.set_permissions(target, overwrite=previous, reason="Откат архивирования")
            except Exception:
                logger.exception("Не удалось восстановить права %s в %s", target.id, channel.id)
                failed.append(str(target.id))
        message = "Архивирование не завершено. Прежние права восстановлены."
        if failed:
            message = "Архивирование не завершено. Проверь права вручную для ID: " + ", ".join(failed)
        raise TeamError(message) from exc


class DeleteVoiceView(discord.ui.View):
    def __init__(self, guild_id, author_id, role_id, channel_ids, voice_category_id=None):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.author_id = author_id
        self.role_id = role_id
        self.channel_ids = frozenset(channel_ids)
        self.voice_category_id = (voice_category_id if voice_category_id is not None
                                  else settings.TEAM_VOICE_CATEGORY_ID)
        self.finished = False
        self.message = None

    async def interaction_check(self, interaction):
        allowed = (interaction.guild_id == self.guild_id
                   and interaction.user.id == self.author_id
                   and admin_role(interaction.user) is not None)
        if not allowed:
            await interaction.response.send_message("Подтвердить может только автор команды с ролью организатора.", ephemeral=True)
        return allowed

    async def on_timeout(self):
        if self.finished:
            return
        self.finished = True
        for item in self.children:
            item.disabled = True
        if self.message is not None:
            try:
                await self.message.edit(content="Время подтверждения истекло. Голосовые каналы сохранены. Текстовый канал остаётся архивом.", view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="Удалить голосовые каналы", style=discord.ButtonStyle.danger)
    async def delete_channels(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.finished:
            await interaction.response.send_message("Это подтверждение уже обработано.", ephemeral=True)
            return
        self.finished = True
        await interaction.response.defer()
        removed, skipped, failed = [], [], []
        try:
            roles = await interaction.guild.fetch_roles()
            role = discord.utils.get(roles, id=self.role_id)
            for channel_id in self.channel_ids:
                if not is_team_role(role, admin_role(interaction.user)):
                    skipped.append(channel_id)
                    continue
                try:
                    channel = await interaction.guild.fetch_channel(channel_id)
                    if not voice_channels_for_role([channel], role, self.voice_category_id):
                        skipped.append(channel_id)
                        continue
                    await channel.delete(reason=f"Архив команды; организатор {interaction.user.id}")
                    removed.append(channel_id)
                except (discord.NotFound, discord.InvalidData):
                    skipped.append(channel_id)
                except discord.HTTPException:
                    logger.exception("Ошибка удаления голосового канала %s", channel_id)
                    failed.append(channel_id)
            text = f"Удалено голосовых каналов: {len(removed)}. Пропущено: {len(skipped)}. Текстовый канал остаётся архивом."
            if failed:
                text += " Не удалось удалить ID: " + ", ".join(map(str, failed))
        except Exception:
            logger.exception("Ошибка подтверждения удаления голосовых каналов")
            text = "Не удалось проверить голосовые каналы. Повтори /archive для нового подтверждения."
        finally:
            self.stop()
        await interaction.edit_original_response(content=text, view=None)

    @discord.ui.button(label="Оставить голосовые каналы", style=discord.ButtonStyle.secondary)
    async def keep_channels(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.finished:
            await interaction.response.send_message("Это подтверждение уже обработано.", ephemeral=True)
            return
        self.finished = True
        self.stop()
        await interaction.response.edit_message(content="Голосовые каналы сохранены. Текстовый канал остаётся архивом.", view=None)


class TeamCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.creating = set()
        self.archiving = set()

    async def interaction_check(self, interaction):
        guild = interaction.guild
        if guild is None or (settings.TEAM_GUILD_ID is not None and guild.id != settings.TEAM_GUILD_ID):
            raise TeamError("Команда недоступна на этом сервере.")
        if admin_role(interaction.user) is None:
            raise TeamError("Нужна роль организатора команд.")
        if settings.TEAM_GUILD_ID is None and not any(
            isinstance(guild.get_channel(category_id), discord.CategoryChannel)
            for category_id in (settings.TEAM_TEXT_CATEGORY_ID, settings.TEAM_VOICE_CATEGORY_ID)
        ):
            raise TeamError("Для сервера без категорий по умолчанию укажи TEAM_GUILD_ID в настройках бота.")
        return True

    async def cog_app_command_error(self, interaction, error):
        original = getattr(error, "original", error)
        if isinstance(original, TeamError):
            text = str(original)
        elif isinstance(original, discord.InvalidData):
            logger.error("Неподдерживаемый канал при выполнении команды: %s", original,
                         exc_info=(type(original), original, original.__traceback__))
            text = "Discord вернул неподдерживаемый тип выбранного канала. Вызови команду в обычном текстовом канале."
        else:
            logger.error("Ошибка команды команды/архив: %s", error, exc_info=(type(error), error, error.__traceback__))
            text = "Не удалось выполнить команду. Проверь права бота и журнал ошибок."
        if interaction.response.is_done():
            await interaction.followup.send(text, ephemeral=True)
        else:
            await interaction.response.send_message(text, ephemeral=True)

    @app_commands.command(name="create-team", description="Создать командную роль и закрытые каналы")
    @app_commands.guild_only()
    @app_commands.rename(first_member="first-member", second_member="second-member", third_member="third-member",
                         fourth_member="fourth-member", fifth_member="fifth-member", sixth_member="sixth-member",
                         seventh_member="seventh-member", eighth_member="eighth-member",
                         text_category="text-category", voice_category="voice-category")
    @app_commands.describe(team="Название команды; для архивирования нужны скобки, например [KTH] Team",
                           text_category="Категория текстового канала (по умолчанию из настроек)",
                           voice_category="Категория голосового канала (по умолчанию из настроек)")
    async def create_team(self, interaction: discord.Interaction, team: str,
                          first_member: discord.Member, second_member: discord.Member,
                          third_member: discord.Member | None = None, fourth_member: discord.Member | None = None,
                          fifth_member: discord.Member | None = None, sixth_member: discord.Member | None = None,
                          seventh_member: discord.Member | None = None, eighth_member: discord.Member | None = None,
                          text_category: discord.CategoryChannel | None = None,
                          voice_category: discord.CategoryChannel | None = None):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        if guild.id in self.creating:
            raise TeamError("Другая команда ещё создаётся. Подожди завершения.")
        name = team.strip()
        if not 1 <= len(name) <= 100 or name.casefold() in ("@everyone", "@here"):
            raise TeamError("Название должно содержать от 1 до 100 символов и не быть @everyone или @here.")
        members = [m for m in (first_member, second_member, third_member, fourth_member,
                               fifth_member, sixth_member, seventh_member, eighth_member) if m is not None]
        if len({m.id for m in members}) != len(members):
            raise TeamError("Каждый участник должен быть указан один раз.")
        permissions = guild.me.guild_permissions
        if not permissions.manage_roles or not permissions.manage_channels:
            raise TeamError("Боту нужны права «Управлять ролями» и «Управлять каналами».")
        self.creating.add(guild.id)
        try:
            roles = await guild.fetch_roles()
            if any(role.name.casefold() == name.casefold() for role in roles):
                raise TeamError("Роль с таким названием уже существует.")
            text_category = await resolve_category(guild, text_category, settings.TEAM_TEXT_CATEGORY_ID, "Текстовая категория")
            voice_category = await resolve_category(guild, voice_category, settings.TEAM_VOICE_CATEGORY_ID, "Голосовая категория")
            helpers = await helper_bot_members(guild)
            role, text, voice = await create_team_resources(
                guild, name, members, text_category, voice_category, admin_role(interaction.user),
                reason=f"Создание команды; организатор {interaction.user.id}",
                helper_bots=helpers,
            )
            await interaction.followup.send(f"Команда {role.mention} создана. Участников: {len(members)}.\n{text.mention} · {voice.mention}",
                                            ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
        finally:
            self.creating.discard(guild.id)

    @app_commands.command(name="archive", description="Закрыть командный чат для записи и сохранить доступ участникам")
    @app_commands.guild_only()
    @app_commands.rename(text_category="text-category", voice_category="voice-category")
    @app_commands.describe(role="Роль с [ ]; без параметра - список подходящих ролей этого канала",
                           text_category="Категория текущего текстового канала (по умолчанию из настроек)",
                           voice_category="Категория голосовых каналов (по умолчанию из настроек)")
    async def archive(self, interaction: discord.Interaction, role: discord.Role | None = None,
                      text_category: discord.CategoryChannel | None = None,
                      voice_category: discord.CategoryChannel | None = None):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        if role is not None and not has_team_brackets(role.name):
            raise TeamError("Архивировать можно только роль с квадратными скобками [ ], например [KTH] Team.")
        if interaction.channel_id in self.archiving:
            raise TeamError("Этот канал уже архивируется.")
        self.archiving.add(interaction.channel_id)
        try:
            channel = await guild.fetch_channel(interaction.channel_id)
            text_category = await resolve_category(guild, text_category, settings.TEAM_TEXT_CATEGORY_ID, "Текстовая категория")
            if not isinstance(channel, discord.TextChannel) or channel.category_id != text_category.id:
                raise TeamError("Вызови /archive в текстовом канале команды, в настроенной категории или выбранной text-category.")
            roles = await guild.fetch_roles()
            staff = admin_role(interaction.user)
            eligible = [r for r in roles if is_team_role(r, staff) and role_can_view(channel, r)]
            if role is None:
                names = "\n".join(f"{r.name} (ID: {r.id})" for r in eligible) or "Нет командных ролей с явным доступом."
                if len(names) <= 1800:
                    await interaction.followup.send("Укажи роль в /archive. Роли с доступом:\n" + names,
                                                    ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
                else:
                    await interaction.followup.send("Укажи роль в /archive. Роли с доступом:", ephemeral=True,
                                                    file=discord.File(io.BytesIO(names.encode("utf-8")), filename="roles.txt"))
                return
            role = discord.utils.get(eligible, id=role.id)
            if role is None:
                raise TeamError("Выбери командную роль с [ ] и явным доступом к этому каналу.")
            if not channel.permissions_for(guild.me).manage_roles:
                raise TeamError("Боту нужно право «Управлять ролями» в этом канале для изменения доступа.")
            # REST pagination avoids incomplete caches and the old 1000-member cutoff.
            members = [member async for member in guild.fetch_members(limit=None) if role in member.roles]
            voice_category = await resolve_category(guild, voice_category, settings.TEAM_VOICE_CATEGORY_ID, "Голосовая категория")
            voice = await fetch_voice_candidates(guild, role, voice_category.id)
            await archive_permissions(channel, role, members, reason=f"Архив команды; организатор {interaction.user.id}")
            summary = f"Канал переведён в архив. Доступ к чтению сохранён для {len(members)} участников."
            try:
                await channel.send(f"Канал архивирован <t:{int(discord.utils.utcnow().timestamp())}:D> организатором <@{interaction.user.id}>.",
                                   allowed_mentions=discord.AllowedMentions.none())
            except discord.HTTPException:
                logger.exception("Права архива сохранены, но уведомление не отправлено в %s", channel.id)
                summary += " Не удалось отправить публичное уведомление."
            participants = "\n".join(f"{m} (ID: {m.id})" for m in members) or "Участников с ролью нет."
            await interaction.followup.send(summary, ephemeral=True,
                                            file=discord.File(io.BytesIO(participants.encode("utf-8")), filename="participants.txt"))
            if voice:
                view = DeleteVoiceView(guild.id, interaction.user.id, role.id, [c.id for c in voice], voice_category.id)
                names = ", ".join(c.mention for c in voice)
                view.message = await interaction.followup.send(
                    "Текстовый канал уже архивирован. Удалить голосовые каналы?\n" + names[:1700],
                    view=view, ephemeral=True, wait=True,
                )
        finally:
            self.archiving.discard(interaction.channel_id)


async def setup(bot):
    await bot.add_cog(TeamCommands(bot))
