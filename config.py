import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
LOCAL_ENV = Path(__file__).parent / ".env"

load_dotenv(ROOT_ENV)
load_dotenv(LOCAL_ENV, override=True)


@dataclass
class Config:
    bot_token: str
    test_guild_id: int | None
    bot_ops_webhook: str | None
    openrouter_api_key: str | None
    openrouter_model: str


def load_config() -> Config:
    return Config(
        bot_token=os.environ.get("DISCORD_BOT_TOKEN", ""),
        test_guild_id=int(gid) if (gid := os.environ.get("TEST_GUILD_ID")) else None,
        bot_ops_webhook=os.environ.get("BOT_OPS_WEBHOOK_URL") or None,
        openrouter_api_key=os.environ.get("OPENROUTER_API_KEY") or None,
        openrouter_model=os.environ.get("OPENROUTER_MODEL") or "openrouter/free",
    )
