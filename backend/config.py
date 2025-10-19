from dotenv import load_dotenv
import os
from ossapi import OssapiAsync
from pydantic_settings import BaseSettings
from pathlib import Path

# Определяем путь к .env относительно корня проекта
BASE_DIR = Path(__file__).resolve().parent  # Корневая директория проекта
ENV_FILE = BASE_DIR / ".env"
if not os.path.exists(ENV_FILE):
    # Корневая директория проекта
    BASE_DIR = Path(__file__).resolve().parent.parent
    ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    OSU_CLIENT_ID: int
    OSU_CLIENT_SECRET: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_ROOT_PASSWORD: str
    MYSQL_DATABASE: str
    MYSQL_PORT: int
    MYSQL_IP: str
    JWT_SECRET: str
    BOT_API_KEY: str
    SERVER_PORT: int
    SERVER_HOST: str

    @property
    def async_database_url(self) -> str:
        return f"mysql+asyncmy://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_IP}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        extra = "ignore"  # TODO: maybe this is bad but I don't think so..


settings = Settings()
OSU_API_ASYNC = OssapiAsync(settings.OSU_CLIENT_ID, settings.OSU_CLIENT_SECRET)
