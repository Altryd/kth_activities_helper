import pytest
from osu_api.get_user import get_user
from backend.config import settings
from ossapi import Ossapi


@pytest.mark.parametrize("test_input", [
    {"username_or_id": "Boriska", "type": "username", "result_id": 6560308, "resultNone": False},
    {"username_or_id": 6560308, "type": "id", "resultNone": False},
    {"username_or_id": 1345541342423, "type": "id", "resultNone": True}
])
def test_get_user(test_input):
    api = Ossapi(settings.OSU_CLIENT_ID, settings.OSU_CLIENT_SECRET)
    username_or_id = test_input["username_or_id"]
    user = get_user(api, username_or_id)
    assert (user is None) is test_input["resultNone"]
    if not test_input["resultNone"] and test_input["type"] == "username":
        assert user.id == test_input["result_id"]
