from fastapi import FastAPI, Depends, HTTPException, Header, status, Request
from pydantic import BaseModel
from typing import Optional, Union
import jwt
from backend.config import settings


# Проверка JWT
def verify_jwt(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload["sub"]  # Предполагаем, что в JWT хранится user_id или discord_id
    except jwt.InvalidTokenError:
        return None


def verify_auth(request: Request) -> dict:
    """
    Проверяет либо JWT токен, либо API ключ бота
    Возвращает информацию о пользователе/боте
    """
    authorization = request.headers.get("Authorization")
    # print(f"Raw headers: {dict(request.headers)}")  # Для отладки
    # print(f"Authorization header: {authorization}")  # Для отладки

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )

    token = authorization.split(" ")[1]

    # Сначала проверяем, это API ключ бота?
    if token == settings.BOT_API_KEY:
        return {"type": "bot", "user_id": None}

    # Если не API ключ, то проверяем JWT
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid JWT token")
        return {"type": "user", "user_id": user_id}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# def optional_auth(authorization: Optional[str] = Header(None, alias="Authorization")) -> Optional[dict]:
def optional_auth(request: Request) -> Optional[dict]:
    """Возвращает None если нет авторизации, или данные пользователя/бота"""
    authorization = request.headers.get("Authorization")
    # print(f"Raw headers: {dict(request.headers)}")  # Для отладки
    # print(f"Authorization header: {authorization}")  # Для отладки

    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ")[1]

    if token == settings.BOT_API_KEY:
        return {"type": "bot"}

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return {"type": "user", "user_id": payload.get("user_id")}
    except jwt.PyJWTError:
        return None
