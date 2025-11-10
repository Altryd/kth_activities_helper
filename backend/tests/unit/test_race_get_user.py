import pytest
from ossapi import OssapiAsync
from backend.config import settings, OSU_API_ASYNC
import asyncio
from backend.osu_api.get_user import get_user, get_users
from fastapi import FastAPI, HTTPException


@pytest.mark.asyncio
async def test_concurrent_get_user(monkeypatch):
    app = FastAPI()
    app.state.osu_api = OSU_API_ASYNC

    # Эмулируем одновременные запросы
    users = await asyncio.gather(
        get_user("Boriska", app.state.osu_api),
        get_user(6560308, app.state.osu_api),
        get_user("tybug", app.state.osu_api)
    )

    assert users[0] is not None
    assert users[0].id == 6560308
    assert users[1] is not None
    assert users[2] is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("test_input", [
    {"username_or_id": "Boriska", "type": "username",
        "result_id": 6560308, "resultNone": False},
    {"username_or_id": 6560308, "type": "id", "resultNone": False},
    {"username_or_id": 1345541342423, "type": "id",
        "resultNone": True, "raises": HTTPException},
    {"username_or_id": "", "type": "username",
        "resultNone": True, "raises": HTTPException},
    {"username_or_id": None, "type": "username",
        "resultNone": True, "raises": HTTPException}
])
async def test_get_user(test_input):
    osu_api = OssapiAsync(settings.OSU_CLIENT_ID, settings.OSU_CLIENT_SECRET)
    username_or_id = test_input["username_or_id"]
    if "raises" in test_input:
        with pytest.raises(test_input["raises"]):
            await get_user(username_or_id, osu_api)
    else:
        user = await get_user(username_or_id, osu_api)
        assert (user.id is None) is test_input["resultNone"]
        if not test_input["resultNone"] and test_input["type"] == "username":
            assert user.id == test_input["result_id"]


@pytest.mark.asyncio
@pytest.mark.parametrize("test_input", [
    {"ids": [6560308, 11234356, 11359985], "result_usernames": [
        "Boriska", "Meowzarte", "8mi8", "lol"], "valid_return_len": 3},
    {"ids": [6560308, 11234356, 3497238463287412], "result_usernames": [
        "Boriska", "Meowzarte"], "valid_return_len": 2},
    {"ids": [3497238463287412], "result_usernames": [], "valid_return_len": 0},
    {"ids": [],
     "result_usernames": [],
     "valid_return_len": 0,
     "raises": HTTPException},
    {"ids": [0, -1, -2], "result_usernames": [],
        "valid_return_len": 0, "raises": HTTPException},
    {"ids": "",
     "result_usernames": [],
     "valid_return_len": 0,
     "raises": HTTPException},
    {"ids": ["6560308", "1337228"], "result_usernames": [],
        "valid_return_len": 0, "raises": HTTPException},
])
async def test_get_users(test_input):
    osu_api = OssapiAsync(settings.OSU_CLIENT_ID, settings.OSU_CLIENT_SECRET)
    ids = test_input["ids"]
    valid_return_len = test_input["valid_return_len"]
    if "raises" in test_input:
        with pytest.raises(test_input["raises"]):
            await get_users(ids, osu_api)
    else:
        users = await get_users(ids, osu_api)
        assert len(users) == valid_return_len
        result_usernames = test_input["result_usernames"]
        for user, needed_username in zip(users, result_usernames):
            assert user.username == needed_username
            assert user.statistics_rulesets.osu.pp > 10.0
            # pp is user.statistics_rulesets.osu.pp
