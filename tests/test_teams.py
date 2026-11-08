from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from discord_bot.commands import teams
from discord_bot.config import settings

pytestmark = pytest.mark.asyncio


def make_role(role_id=50, name="[T] Team"):
    role = MagicMock(spec=discord.Role)
    role.id, role.name, role.mention = role_id, name, f"<@&{role_id}>"
    role.is_default.return_value = False
    role.managed = False
    role.permissions = discord.Permissions.none()
    role.delete = AsyncMock()
    return role


def make_member(member_id=60, roles=()):
    member = MagicMock(spec=discord.Member)
    member.id, member.roles = member_id, list(roles)
    member.add_roles = AsyncMock()
    return member


def make_channel(channel_id, category_id, role, kind=discord.TextChannel):
    channel = MagicMock(spec=kind)
    channel.id, channel.category_id, channel.name = channel_id, category_id, "same-name"
    channel.mention = f"<#{channel_id}>"
    channel.overwrites = {role: discord.PermissionOverwrite(view_channel=True, attach_files=True)}
    channel.overwrites_for.side_effect = lambda target: discord.PermissionOverwrite.from_pair(
        *channel.overwrites.get(target, discord.PermissionOverwrite()).pair())
    channel.permissions_for.return_value = discord.Permissions.all()
    channel.set_permissions, channel.send, channel.delete = AsyncMock(), AsyncMock(), AsyncMock()
    return channel


def make_interaction(guild, staff, channel_id=40):
    return SimpleNamespace(
        guild=guild, guild_id=guild.id, channel_id=channel_id,
        user=make_member(60, [staff]),
        response=SimpleNamespace(defer=AsyncMock(), send_message=AsyncMock(), edit_message=AsyncMock()),
        followup=SimpleNamespace(send=AsyncMock()), edit_original_response=AsyncMock(),
    )


def make_guild():
    guild = MagicMock(spec=discord.Guild)
    guild.id = 1
    guild.me, guild.default_role = make_member(999), make_role(1, "@everyone")
    guild.me.guild_permissions = discord.Permissions.all()
    guild.get_channel.return_value = MagicMock(spec=discord.CategoryChannel)
    guild.fetch_roles = AsyncMock(return_value=[])
    return guild


async def test_create_team_assigns_role_and_both_private_channels():
    guild, staff, role = make_guild(), make_role(10, "staff"), make_role()
    members = [make_member(60), make_member(61)]
    guild.create_role = AsyncMock(return_value=role)
    guild.create_text_channel, guild.create_voice_channel = AsyncMock(), AsyncMock()
    result = await teams.create_team_resources(guild, "Team", members, 20, 30, staff, "test")
    assert result[0] is role
    for member in members:
        member.add_roles.assert_awaited_once_with(role, reason="test")
    overwrites = guild.create_text_channel.call_args.kwargs["overwrites"]
    assert overwrites[guild.default_role].view_channel is False
    assert overwrites[role].view_channel is True
    assert overwrites[guild.me].manage_roles is True


async def test_create_failure_rolls_back_channels_and_role():
    guild, role, text, staff = make_guild(), make_role(), MagicMock(), make_role(10)
    text.delete = AsyncMock()
    guild.create_role = AsyncMock(return_value=role)
    guild.create_text_channel = AsyncMock(return_value=text)
    guild.create_voice_channel = AsyncMock(side_effect=RuntimeError("denied"))
    with pytest.raises(teams.TeamError, match="Созданные ресурсы удалены"):
        await teams.create_team_resources(guild, "Team", [make_member()], 20, 30, staff, "test")
    role.delete.assert_awaited_once()
    text.delete.assert_awaited_once()


async def test_failed_cleanup_reports_resource_id():
    guild, role = make_guild(), make_role()
    role.delete.side_effect = RuntimeError("denied")
    guild.create_role = AsyncMock(return_value=role)
    member = make_member()
    member.add_roles.side_effect = RuntimeError("denied")
    with pytest.raises(teams.TeamError, match="50"):
        await teams.create_team_resources(guild, "Team", [member], 20, 30, make_role(10), "test")


async def test_create_rejects_duplicates_and_releases_busy_flag():
    guild, staff = make_guild(), make_role(10)
    cog, ctx = teams.TeamCommands(None), make_interaction(guild, staff)
    member = make_member()
    with pytest.raises(teams.TeamError, match="один раз"):
        await cog.create_team.callback(cog, ctx, "Team", member, member)
    guild.fetch_roles.return_value = [make_role(name="Team")]
    with pytest.raises(teams.TeamError, match="уже существует"):
        await cog.create_team.callback(cog, ctx, "Team", member, make_member(61))
    assert not cog.creating


async def test_archiving_preserves_other_overwrite_bits():
    role, member = make_role(), make_member()
    channel = make_channel(40, 20, role)
    channel.overwrites[member] = discord.PermissionOverwrite(attach_files=False, manage_messages=True)
    await teams.archive_permissions(channel, role, [member], "test")
    role_permissions = channel.set_permissions.call_args_list[0].kwargs["overwrite"]
    user_permissions = channel.set_permissions.call_args_list[1].kwargs["overwrite"]
    assert role_permissions.attach_files is True
    assert role_permissions.send_messages is False
    assert user_permissions.view_channel is True
    assert user_permissions.read_message_history is True
    assert user_permissions.send_messages_in_threads is False
    assert user_permissions.attach_files is False
    assert user_permissions.manage_messages is True


async def test_partial_archive_restores_preexisting_permissions():
    role, first, second = make_role(), make_member(60), make_member(61)
    channel = make_channel(40, 20, role)
    channel.set_permissions.side_effect = [None, None, RuntimeError("denied"), None, None, None]
    with pytest.raises(teams.TeamError, match="Прежние права восстановлены"):
        await teams.archive_permissions(channel, role, [first, second], "test")
    calls = channel.set_permissions.call_args_list
    assert calls[3].args[0] is second and calls[3].kwargs["overwrite"] is None
    assert calls[4].args[0] is first and calls[4].kwargs["overwrite"] is None
    assert calls[5].args[0] is role
    assert calls[5].kwargs["overwrite"].send_messages is None


async def test_archive_fetches_all_members_and_works_beyond_1000(monkeypatch):
    guild, staff, role = make_guild(), make_role(10), make_role()
    channel = make_channel(40, settings.TEAM_TEXT_CATEGORY_ID, role)
    guild.fetch_roles = AsyncMock(return_value=[role, staff])
    guild.fetch_channels = AsyncMock(return_value=[channel])
    members = [make_member(n + 100, [role]) for n in range(1001)]

    async def fetch_members(*, limit):
        assert limit is None
        for member in members:
            yield member

    guild.fetch_members = fetch_members
    apply = AsyncMock()
    monkeypatch.setattr(teams, "archive_permissions", apply)
    cog, ctx = teams.TeamCommands(None), make_interaction(guild, staff)
    await cog.archive.callback(cog, ctx, role)
    assert len(apply.call_args.args[2]) == 1001
    assert not cog.archiving


async def test_archive_rejects_unrelated_channel_and_role():
    guild, staff, role = make_guild(), make_role(10), make_role()
    channel = make_channel(40, 999, role)
    guild.fetch_roles = AsyncMock(return_value=[role, staff])
    guild.fetch_channels = AsyncMock(return_value=[channel])
    cog, ctx = teams.TeamCommands(None), make_interaction(guild, staff)
    with pytest.raises(teams.TeamError, match="настроенной категории"):
        await cog.archive.callback(cog, ctx, role)
    channel.category_id = settings.TEAM_TEXT_CATEGORY_ID
    channel.overwrites = {}
    with pytest.raises(teams.TeamError, match="явным доступом"):
        await cog.archive.callback(cog, ctx, role)
    channel.set_permissions.assert_not_awaited()
    assert not cog.archiving


async def test_delete_matches_ids_not_names_and_rechecks_access():
    guild, role, staff = make_guild(), make_role(), make_role(10)
    requested = make_channel(70, 30, role, discord.VoiceChannel)
    same_name = make_channel(71, 30, role, discord.VoiceChannel)
    moved = make_channel(72, 999, role, discord.VoiceChannel)
    lost_access = make_channel(73, 30, role, discord.VoiceChannel)
    lost_access.overwrites = {}
    guild.fetch_roles = AsyncMock(return_value=[role, staff])
    guild.fetch_channels = AsyncMock(return_value=[requested, same_name, moved, lost_access])
    view = teams.DeleteVoiceView(1, 60, role.id, [70, 72, 73])
    ctx = make_interaction(guild, staff)
    assert await view.interaction_check(ctx)
    await view.delete_channels.callback(ctx)
    requested.delete.assert_awaited_once()
    for channel in (same_name, moved, lost_access):
        channel.delete.assert_not_awaited()
    await view.delete_channels.callback(ctx)
    requested.delete.assert_awaited_once()


async def test_delete_requires_original_author_and_current_admin_role():
    guild, staff = make_guild(), make_role(10)
    ctx = make_interaction(guild, staff)
    view = teams.DeleteVoiceView(1, 60, 50, [70])
    ctx.user.id = 61
    assert not await view.interaction_check(ctx)
    ctx.user.id, ctx.user.roles = 60, []
    assert not await view.interaction_check(ctx)
    view.stop()


async def test_cancel_and_timeout_keep_voice_channels():
    ctx = make_interaction(make_guild(), make_role(10))
    view = teams.DeleteVoiceView(1, 60, 50, [70])
    await view.keep_channels.callback(ctx)
    assert view.finished
    assert "Текстовый канал остаётся архивом" in ctx.response.edit_message.call_args.kwargs["content"]
    timed = teams.DeleteVoiceView(1, 60, 50, [70])
    timed.message = SimpleNamespace(edit=AsyncMock())
    await timed.on_timeout()
    assert all(item.disabled for item in timed.children)
    assert timed.finished
    timed.stop()


async def test_module_checks_server_role_and_categories():
    guild, staff = make_guild(), make_role(10)
    cog, ctx = teams.TeamCommands(None), make_interaction(guild, staff)
    assert await cog.interaction_check(ctx)
    guild.id = 2
    with pytest.raises(teams.TeamError, match="этом сервере"):
        await cog.interaction_check(ctx)
    guild.id, ctx.user.roles = 1, []
    with pytest.raises(teams.TeamError, match="роль организатора"):
        await cog.interaction_check(ctx)
    ctx.user.roles = [staff]
    guild.get_channel.return_value = None
    with pytest.raises(teams.TeamError, match="категории"):
        await cog.interaction_check(ctx)
