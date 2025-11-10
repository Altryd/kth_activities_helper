import pytest
import requests
from backend.config import settings
import jwt
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_pairs():
    response = requests.post(f"http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/create_pairs",
                             json={"temporary_used_players": [],
                                   "pairs_correction": []})
    print(response.json())
    assert response.status_code == 200


def create_test_jwt(user_id: int, expires_in_minutes: int = 30) -> str:
    """Создает тестовый JWT токен"""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=expires_in_minutes),
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    return token
