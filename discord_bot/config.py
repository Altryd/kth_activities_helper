from dotenv import load_dotenv
import os
from ossapi import OssapiAsync
from pydantic_settings import BaseSettings
from pathlib import Path

# Определяем путь к .env относительно корня проекта
BASE_DIR = Path(__file__).resolve().parent  # Корневая директория проекта
ENV_FILE = BASE_DIR / ".env"
if not os.path.exists(ENV_FILE):
    BASE_DIR = Path(__file__).resolve().parent.parent  # Корневая директория проекта
    ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    DISCORD_KTH_TOKEN: str
    BOT_API_KEY: str
    SERVER_PORT: str
    SERVER_HOST: str
    SERVER_PROTOCOL: str
    ROLE_X_ID: int
    BOTS_COMMAND_ID: int
    BASE_MUTE_CHANCE: int
    OVERKILL: int
    CHANCE_INCREASE_PER_STREAK: int
    BASE_MUTE_MINUTES: int
    OVERKILL_MUTE_MULTIPLIER: int
    MINUTES_INCREASE_PER_STREAK: int
    GIF_FOLDER: str

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        extra = "ignore"  # TODO: maybe this is bad but I don't think so..


def get_auth_headers():
    return {
        "Authorization": f"Bearer {settings.BOT_API_KEY}",
        "Content-Type": "application/json"
    }

settings = Settings()
# OSU_API_ASYNC = OssapiAsync(settings.OSU_CLIENT_ID, settings.OSU_CLIENT_SECRET)
