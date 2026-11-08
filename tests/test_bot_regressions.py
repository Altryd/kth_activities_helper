import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from discord_bot.commands import roulette, userinfo
from discord_bot.config import settings
from discord_bot.demo_kth import KTHBot
from discord_bot.utils import api

pytestmark = pytest.mark.asyncio


def interaction():
    return SimpleNamespace(
        user=SimpleNamespace(id=123),
        response=SimpleNamespace(defer=AsyncMock(), send_message=AsyncMock(), is_done=lambda: True),
        followup=SimpleNamespace(send=AsyncMock()),
    )


def roulette_message():
    return SimpleNamespace(
        author=SimpleNamespace(id=123, bot=False, get_role=lambda _: True, timeout=AsyncMock()),
        guild=SimpleNamespace(get_role=lambda _: None),
        role_mentions=[SimpleNamespace(id=settings.ROLE_X_ID)],
        channel=SimpleNamespace(id=settings.BOTS_COMMAND_ID), reply=AsyncMock(),
    )


async def test_setup_loads_all_commands_without_rating_and_ready_does_not_reload():
    bot = KTHBot(command_prefix="!", intents=discord.Intents.none())
    bot.tree.sync = AsyncMock(return_value=[])
    async with bot:
        await bot.setup_hook()
        names = {command.name for command in bot.tree.get_commands()}
        assert {"create-team", "archive", "userinfo", "userinfo_id", "register", "roulette_stats"} <= names
        assert "rating" not in names
        create = bot.tree.get_command("create-team")
        assert len(create.parameters) == 9
        assert create.parameters[1].display_name == "first-member"
        await bot.on_ready()
        await bot.on_ready()
        bot.tree.sync.assert_awaited_once()
        assert len(bot.extensions) == 3


@pytest.mark.parametrize("name,api_name,args", [
    ("userinfo", "get_user_by_username", ("player",)),
    ("userinfo_id", "get_user_by_id", (123,)),
    ("register", "register_user", ()),
])
async def test_commands_defer_once_and_reach_api(monkeypatch, name, api_name, args):
    call = AsyncMock(return_value={})
    monkeypatch.setattr(userinfo, api_name, call)
    monkeypatch.setattr(userinfo, "get_embed_for_userinfo", lambda _: discord.Embed(title="ok"))
    ctx = interaction()
    cog = userinfo.UserInfoCommands(None)
    await getattr(cog, name).callback(cog, ctx, *args)
    ctx.response.defer.assert_awaited_once()
    call.assert_awaited_once()
    ctx.followup.send.assert_awaited_once()


async def test_roulette_read_failure_releases_user_and_next_attempt_works(monkeypatch):
    get_stats = AsyncMock(side_effect=[api.APIError("Сервис недоступен"), {"streak_current": 0}])
    update = AsyncMock()
    monkeypatch.setattr(roulette, "get_roulette_stats", get_stats)
    monkeypatch.setattr(roulette, "update_roulette_stats", update)
    monkeypatch.setattr(roulette.random, "randint", lambda *_: 1)
    cog, message = roulette.RouletteCommands(None), roulette_message()
    await cog.on_message(message)
    assert not cog.history_ids
    assert "Сервис недоступен" in message.reply.call_args.args[0]
    await cog.on_message(message)
    update.assert_awaited_once()
    assert not cog.history_ids


async def test_roulette_write_failure_does_not_retry_or_leave_user_locked(monkeypatch):
    monkeypatch.setattr(roulette, "get_roulette_stats", AsyncMock(return_value={"streak_current": 0}))
    update = AsyncMock(side_effect=api.APIError("Ошибка записи"))
    monkeypatch.setattr(roulette, "update_roulette_stats", update)
    cog, message = roulette.RouletteCommands(None), roulette_message()
    await cog.on_message(message)
    update.assert_awaited_once()
    message.author.timeout.assert_not_awaited()
    assert not cog.history_ids


async def test_two_mentions_cannot_start_concurrent_rolls(monkeypatch):
    entered, release = asyncio.Event(), asyncio.Event()

    async def delayed_stats(_):
        entered.set()
        await release.wait()
        return {"streak_current": 0}

    get_stats = AsyncMock(side_effect=delayed_stats)
    update = AsyncMock()
    monkeypatch.setattr(roulette, "get_roulette_stats", get_stats)
    monkeypatch.setattr(roulette, "update_roulette_stats", update)
    cog, message = roulette.RouletteCommands(None), roulette_message()
    first = asyncio.create_task(cog.on_message(message))
    await entered.wait()
    try:
        await cog.on_message(message)
        assert "ожидайте" in message.reply.call_args.args[0]
    finally:
        release.set()
        await first
    get_stats.assert_awaited_once()
    update.assert_awaited_once()
    assert not cog.history_ids


async def test_cancellation_does_not_leave_roulette_locked(monkeypatch):
    monkeypatch.setattr(roulette, "get_roulette_stats", AsyncMock(side_effect=asyncio.CancelledError))
    cog = roulette.RouletteCommands(None)
    with pytest.raises(asyncio.CancelledError):
        await cog.on_message(roulette_message())
    assert not cog.history_ids


async def test_failed_error_reply_still_releases_user(monkeypatch):
    monkeypatch.setattr(roulette, "get_roulette_stats", AsyncMock(side_effect=api.APIError("offline")))
    cog, message = roulette.RouletteCommands(None), roulette_message()
    message.reply.side_effect = RuntimeError("cannot send messages")
    with pytest.raises(RuntimeError):
        await cog.on_message(message)
    assert not cog.history_ids


def mock_response(monkeypatch, status, payload=None, json_error=None):
    response = SimpleNamespace(status=status, json=AsyncMock(return_value=payload, side_effect=json_error))
    request_context = MagicMock()
    request_context.__aenter__ = AsyncMock(return_value=response)
    request_context.__aexit__ = AsyncMock(return_value=False)
    session = MagicMock()
    session.request.return_value = request_context
    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=session)
    session_context.__aexit__ = AsyncMock(return_value=False)
    constructor = MagicMock(return_value=session_context)
    monkeypatch.setattr(api.aiohttp, "ClientSession", constructor)
    return session, response, constructor


async def test_api_handles_non_json_500_without_repeating_post(monkeypatch):
    session, response, constructor = mock_response(monkeypatch, 500, json_error=ValueError("HTML"))
    with pytest.raises(api.APIError, match="временно недоступен"):
        await api.update_roulette_stats("123", 63, True, 1, [])
    session.request.assert_called_once()
    response.json.assert_not_awaited()
    assert constructor.call_args.kwargs["timeout"].total == 15


async def test_api_timeout_becomes_user_facing_error(monkeypatch):
    session, _, _ = mock_response(monkeypatch, 200)
    session.request.side_effect = asyncio.TimeoutError()
    with pytest.raises(api.APIError, match="Не удалось связаться"):
        await api.get_roulette_stats("123")


async def test_api_preserves_validation_errors(monkeypatch):
    mock_response(monkeypatch, 404, {"detail": "User not found"})
    with pytest.raises(api.APIError, match="User not found"):
        await api.get_user_by_id(123)
