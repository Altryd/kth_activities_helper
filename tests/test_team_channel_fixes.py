from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord
import pytest

from discord_bot.commands import teams
from discord_bot.config import settings
from discord_bot.demo_kth import KTHBot
from test_teams import make_guild, make_role, make_member, make_channel, make_category, make_interaction, set_channels

pytestmark = pytest.mark.asyncio


async def test_library_bulk_fetch_reproduces_unknown_type_20():
    guild = make_guild()
    guild._state = SimpleNamespace(http=SimpleNamespace(
        get_all_guild_channels=AsyncMock(return_value=[{"id": "999", "type": 20}]),
    ))
    with pytest.raises(discord.InvalidData, match="Unknown channel type 20"):
        await discord.Guild.fetch_channels(guild)


async def test_category_options_are_discord_category_selectors():
    bot = KTHBot(command_prefix="!", intents=discord.Intents.none())
    bot.tree.sync = AsyncMock(return_value=[])
    async with bot:
        await bot.setup_hook()
        for name in ("create-team", "archive"):
            payload = bot.tree.get_command(name).to_dict(bot.tree)
            options = {option["name"]: option for option in payload["options"]}
            for option_name in ("text-category", "voice-category"):
                assert options[option_name]["type"] == 7
                assert options[option_name]["channel_types"] == [4]
                assert not options[option_name]["required"]


async def test_archive_ignores_unrelated_unknown_channel_type(monkeypatch):
    guild, role, staff = make_guild(), make_role(), make_role(10)
    text = make_channel(40, 20, role)
    voice = make_channel(70, 30, role, discord.VoiceChannel)
    set_channels(guild, text, voice)
    guild.fetch_roles.return_value = [role, staff]

    async def members(**kwargs):
        yield make_member(60, [role])

    guild.fetch_members = members
    update = AsyncMock()
    monkeypatch.setattr(teams, "archive_permissions", update)
    cog, ctx = teams.TeamCommands(None), make_interaction(guild, staff)
    await cog.archive.callback(cog, ctx, role)
    update.assert_awaited_once()
    guild.fetch_channels.assert_not_awaited()
    view = ctx.followup.send.call_args.kwargs["view"]
    assert view.channel_ids == {70}
    await view.delete_channels.callback(ctx)
    voice.delete.assert_awaited_once()
    text.delete.assert_not_awaited()
    guild.fetch_channels.assert_not_awaited()


async def test_create_uses_selected_categories_and_configured_osu_bots():
    guild, role, staff = make_guild(), make_role(), make_role(10)
    text_category, voice_category = make_category(21), make_category(31)
    set_channels(guild, text_category, voice_category)
    guild.create_role = AsyncMock(return_value=role)
    guild.create_text_channel, guild.create_voice_channel = AsyncMock(), AsyncMock()
    cog, ctx = teams.TeamCommands(None), make_interaction(guild, staff)
    await cog.create_team.callback(cog, ctx, "[T] Team", make_member(60), make_member(61),
                                   text_category=text_category, voice_category=voice_category)
    assert guild.create_text_channel.call_args.kwargs["category"] is text_category
    assert guild.create_voice_channel.call_args.kwargs["category"] is voice_category
    assert [call.args[0] for call in guild.fetch_member.call_args_list] == settings.TEAM_HELPER_BOT_IDS
    text_overwrites = guild.create_text_channel.call_args.kwargs["overwrites"]
    voice_overwrites = guild.create_voice_channel.call_args.kwargs["overwrites"]
    helpers = [member for member in text_overwrites if member.id in settings.TEAM_HELPER_BOT_IDS]
    assert len(helpers) == 4
    for helper in helpers:
        assert text_overwrites[helper].view_channel is True
        assert text_overwrites[helper].send_messages is True
        assert text_overwrites[helper].read_message_history is True
        assert text_overwrites[helper].manage_channels is None
        assert helper not in voice_overwrites
        helper.add_roles.assert_not_awaited()


async def test_archive_and_confirmation_remember_custom_categories(monkeypatch):
    guild, role, staff = make_guild(), make_role(), make_role(10)
    text_category, voice_category = make_category(21), make_category(31)
    text = make_channel(40, 21, role)
    selected_voice = make_channel(70, 31, role, discord.VoiceChannel)
    default_voice = make_channel(71, 30, role, discord.VoiceChannel)
    set_channels(guild, text_category, voice_category, text, selected_voice, default_voice)
    guild.fetch_roles.return_value = [role, staff]

    async def members(**kwargs):
        yield make_member(60, [role])

    guild.fetch_members = members
    monkeypatch.setattr(teams, "archive_permissions", AsyncMock())
    cog, ctx = teams.TeamCommands(None), make_interaction(guild, staff)
    await cog.archive.callback(cog, ctx, role, text_category, voice_category)
    view = ctx.followup.send.call_args.kwargs["view"]
    assert view.voice_category_id == 31 and view.channel_ids == {70}
    await view.delete_channels.callback(ctx)
    selected_voice.delete.assert_awaited_once()
    default_voice.delete.assert_not_awaited()


@pytest.mark.parametrize("name", ["Team", "][Team", "[Team", "Team]", "Other role"])
async def test_archive_rejects_unmarked_roles_before_any_channel_request(name):
    guild, role = make_guild(), make_role(name=name)
    ctx, cog = make_interaction(guild, make_role(10)), teams.TeamCommands(None)
    with pytest.raises(teams.TeamError, match="квадратными скобками"):
        await cog.archive.callback(cog, ctx, role)
    guild.fetch_channel.assert_not_awaited()
    guild.fetch_channels.assert_not_awaited()


@pytest.mark.parametrize("name", ["[KTH] Team", "Team []", "Team [ ]", "Team [123]"])
async def test_archive_accepts_paired_bracket_markers(name):
    assert teams.is_team_role(make_role(name=name))


async def test_permission_helper_rejects_unmarked_role():
    role = make_role(name="ordinary role")
    text = make_channel(40, 20, role)
    with pytest.raises(teams.TeamError):
        await teams.archive_permissions(text, role, [], "test")
    text.set_permissions.assert_not_awaited()


async def test_confirmation_rechecks_brackets_after_role_rename():
    guild, role, staff = make_guild(), make_role(), make_role(10)
    voice = make_channel(70, 30, role, discord.VoiceChannel)
    set_channels(guild, voice)
    view = teams.DeleteVoiceView(1, 60, role.id, [70])
    role.name = "ordinary role"
    guild.fetch_roles.return_value = [role, staff]
    await view.delete_channels.callback(make_interaction(guild, staff))
    voice.delete.assert_not_awaited()
    guild.fetch_channel.assert_not_awaited()


@pytest.mark.parametrize("kind", [discord.TextChannel, discord.CategoryChannel, discord.ForumChannel, discord.StageChannel])
async def test_confirmation_never_deletes_non_voice_channels(kind):
    guild, role, staff = make_guild(), make_role(), make_role(10)
    channel = make_channel(70, 30, role, kind)
    set_channels(guild, channel)
    guild.fetch_roles.return_value = [role, staff]
    view = teams.DeleteVoiceView(1, 60, role.id, [70])
    await view.delete_channels.callback(make_interaction(guild, staff))
    channel.delete.assert_not_awaited()


async def test_unknown_type_in_requested_voice_is_skipped_not_deleted():
    guild, role, staff = make_guild(), make_role(), make_role(10)
    guild.fetch_roles.return_value = [role, staff]
    guild.fetch_channel.side_effect = discord.InvalidData("Unknown channel type 20")
    view = teams.DeleteVoiceView(1, 60, role.id, [70])
    ctx = make_interaction(guild, staff)
    await view.delete_channels.callback(ctx)
    assert "Пропущено: 1" in ctx.edit_original_response.call_args.kwargs["content"]


@pytest.mark.parametrize("bad_helper", ["not_a_bot", "not_found"])
async def test_invalid_helper_bot_fails_before_creating_any_resource(bad_helper):
    guild, staff = make_guild(), make_role(10)
    guild.create_role = AsyncMock()
    if bad_helper == "not_a_bot":
        guild.fetch_member.return_value = make_member(123, bot=False)
        guild.fetch_member.side_effect = None
    else:
        guild.fetch_member.side_effect = discord.NotFound(SimpleNamespace(status=404, reason="Not Found"), "missing")
    cog, ctx = teams.TeamCommands(None), make_interaction(guild, staff)
    with pytest.raises(teams.TeamError, match="TEAM_HELPER_BOT_IDS"):
        await cog.create_team.callback(cog, ctx, "[T] Team", make_member(60), make_member(61))
    guild.create_role.assert_not_awaited()
    assert not cog.creating


async def test_category_must_belong_to_current_guild():
    guild = make_guild()
    with pytest.raises(teams.TeamError, match="этого сервера"):
        await teams.resolve_category(guild, make_category(21, guild_id=2), 20, "Текстовая категория")
    guild.fetch_channel.assert_not_awaited()


async def test_archive_list_excludes_unmarked_roles():
    guild, staff, role = make_guild(), make_role(10), make_role()
    unmarked = make_role(51, "Other role")
    text = make_channel(40, 20, role)
    text.overwrites[unmarked] = discord.PermissionOverwrite(view_channel=True)
    set_channels(guild, text)
    guild.fetch_roles.return_value = [role, unmarked, staff]
    cog, ctx = teams.TeamCommands(None), make_interaction(guild, staff)
    await cog.archive.callback(cog, ctx)
    response = ctx.followup.send.call_args.args[0]
    assert role.name in response and unmarked.name not in response
    text.set_permissions.assert_not_awaited()
