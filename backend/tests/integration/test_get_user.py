import pytest
import requests
from backend.config import settings
import jwt
from datetime import datetime, timedelta


def create_test_jwt(user_id: int, expires_in_minutes: int = 30) -> str:
    """Создает тестовый JWT токен"""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=expires_in_minutes),
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    return token


@pytest.mark.parametrize("auth_type,expected_has_private", [
    ("bot_api_key", True),
    ("valid_jwt", True),
    ("invalid_jwt", False),
    ("no_auth", False)
])
@pytest.mark.asyncio
async def test_get_username_auth_types(auth_type, expected_has_private):
    headers = {}

    if auth_type == "bot_api_key":
        headers["Authorization"] = f"Bearer {settings.BOT_API_KEY}"
    elif auth_type == "valid_jwt":
        jwt_token = create_test_jwt(123)
        headers["Authorization"] = f"Bearer {jwt_token}"
    elif auth_type == "invalid_jwt":
        headers["Authorization"] = "Bearer invalid.token.here"

    response = requests.get(f"http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/user/username/Boriska",
                            headers=headers)

    assert response.status_code == 200
    data = response.json()

    if expected_has_private:
        assert "discord_id" in data
        assert "role" in data
    else:
        assert "discord_id" not in data
        assert "role" not in data

    assert "osu_id" in data
    assert "username" in data
    assert "active" in data


@pytest.mark.asyncio
@pytest.mark.parametrize("test_input", [
    {"header_auth": f"Bearer {settings.BOT_API_KEY}"},
])
async def test_get_username_with_auth(test_input):
    response = requests.get(f"http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/user/username/Boriska",
                            headers={"Authorization": test_input["header_auth"]})
    print(response.json())
    data = response.json()
    assert response.status_code == 200
    assert "discord_id" in data
    assert "role" in data
    assert "active" in data
    assert data["discord_id"] is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("test_input", [
    {"header_auth": None},
])
async def test_get_username_with_no_auth(test_input):
    response = requests.get(f"http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/user/username/Boriska",
                            headers={"Authorization": test_input["header_auth"]})
    print(response.json())
    data = response.json()
    assert response.status_code == 200
    assert "discord_id" not in data
    assert "role" not in data
    # публичные поля должны существовать
    assert "osu_id" in data
    assert "username" in data
    assert "active" in data
