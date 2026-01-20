"""Project configuration.

Recommended:
- Put secrets into environment variables (or a .env file).

Environment variables:
- BOT_TOKEN: Telegram bot token
- ADMIN_IDS: comma-separated Telegram user IDs, e.g. "123,456"
- DIGEST_CHANNEL_ID: Telegram channel ID (e.g. -1001234567890)
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: set[int]
    digest_channel_id: int


def _parse_admin_ids(raw: str) -> set[int]:
    raw = (raw or "").strip()
    if not raw:
        return set()
    out: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.add(int(part))
        except ValueError:
            raise ValueError(f"Invalid ADMIN_IDS entry: {part!r}")
    return out


def _parse_channel_id(raw: str) -> int:
    raw = (raw or "").strip()
    if not raw:
        raise RuntimeError("DIGEST_CHANNEL_ID is not set")
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"Invalid DIGEST_CHANNEL_ID: {raw!r}")


def load_settings() -> Settings:
    load_dotenv()

    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is not set")

    admin_ids = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))
    digest_channel_id = _parse_channel_id(os.getenv("DIGEST_CHANNEL_ID", ""))

    return Settings(
        bot_token=token,
        admin_ids=admin_ids,
        digest_channel_id=digest_channel_id,
    )

