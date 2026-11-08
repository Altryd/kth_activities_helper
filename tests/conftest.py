"""Offline regression tests: no real credentials, Discord login or osu! calls."""

import os
from pathlib import Path

TEST_ENV = {
    "ENV_FILE_NAME": "__no_test_env_file__",
    "DISCORD_KTH_TOKEN": "test-token",
    "BOT_API_KEY": "test-key",
    "SERVER_PORT": "8000",
    "SERVER_HOST": "127.0.0.1",
    "SERVER_PROTOCOL": "http",
    "ROLE_X_ID": "101",
    "BOTS_COMMAND_ID": "202",
    "BASE_MUTE_CHANCE": "70",
    "OVERKILL": "95",
    "CHANCE_INCREASE_PER_STREAK": "5",
    "BASE_MUTE_MINUTES": "1",
    "OVERKILL_MUTE_MULTIPLIER": "2",
    "MINUTES_INCREASE_PER_STREAK": "1",
    "GIF_FOLDER": str(Path(__file__).resolve().parents[1] / "discord_bot" / "resources"),
    "TEAM_GUILD_ID": "1",
    "TEAM_ADMIN_ROLE_ID": "10",
    "TEAM_TEXT_CATEGORY_ID": "20",
    "TEAM_VOICE_CATEGORY_ID": "30",
}
os.environ.update(TEST_ENV)
