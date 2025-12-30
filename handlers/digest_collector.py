from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

from aiogram import Router, types

from config import Settings

router = Router()

MSK = timezone(timedelta(hours=3))

BASE_DIR = Path(__file__).resolve().parent.parent
STORE_PATH = BASE_DIR / "data" / "weekly_digest_items.json"


def _load_store() -> list[dict]:
    if not STORE_PATH.exists():
        return []
    try:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_store(items: list[dict]) -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def _title_from_text(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return "Новость"
    first = t.splitlines()[0].strip()
    # если первая строка слишком короткая и дальше есть текст — можно взять вторую
    if len(first) < 10:
        lines = [x.strip() for x in t.splitlines() if x.strip()]
        if len(lines) >= 2:
            first = lines[1]
    return first[:160]


def _post_link(username: str, message_id: int) -> str:
    # Публичный канал: https://t.me/unionpmo/123
    return f"https://t.me/{username}/{message_id}"


@router.channel_post()
async def collect_from_channel(message: types.Message, settings: Settings) -> None:
    """
    Ловим публикации из вашего канала и сохраняем "пункты дайджеста".
    Ссылка формируется на сам пост по message_id.
    """
    if message.chat.id != settings.digest_channel_id:
        return

    text = (message.text or message.caption or "").strip()
    if not text:
        # можно хранить и медиа-посты без текста, но дайджест тогда будет пустым
        return

    title = _title_from_text(text)
    link = _post_link(settings.channel_username, message.message_id)
    ts = datetime.now(MSK).isoformat()

    store = _load_store()

    # дедуп: по message_id
    if any(it.get("message_id") == message.message_id for it in store):
        return

    store.append({
        "ts": ts,
        "message_id": message.message_id,
        "title": title,
        "link": link,
    })
    _save_store(store)
