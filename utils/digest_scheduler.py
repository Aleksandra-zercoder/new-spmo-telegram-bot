from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

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


def _week_range_str(now: datetime) -> str:
    end = now.date()
    start = (now - timedelta(days=7)).date()
    return f"{start.strftime('%d.%m')}–{end.strftime('%d.%m')}"


def build_digest_text(*, max_items: int = 20) -> tuple[str, list[dict]]:
    """
    Возвращает (text, week_items_used)
    """
    now = datetime.now(MSK)
    since = now - timedelta(days=7)
    period = _week_range_str(now)

    store = _load_store()

    week_items: list[dict] = []
    for it in store:
        ts = it.get("ts", "")
        try:
            dt = datetime.fromisoformat(ts)
        except Exception:
            dt = now
        if dt >= since:
            week_items.append(it)

    if not week_items:
        text = f"🗞 <b>Дайджест недели ({period})</b>\n\nНа этой неделе — без публикаций для дайджеста."
        return text, []

    lines = [f"🗞 <b>Дайджест недели ({period})</b>\n"]
    for i, it in enumerate(week_items[:max_items], start=1):
        title = (it.get("title") or "Новость").strip().replace("\n", " ")
        link = (it.get("link") or "").strip()
        lines.append(f"{i}) {title}\n{link}")

    return "\n\n".join(lines), week_items[:max_items]


def clear_store() -> None:
    _save_store([])
