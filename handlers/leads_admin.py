from __future__ import annotations

from pathlib import Path
from aiogram import Router, types
from aiogram.filters import Command

from config import Settings
from utils.json_loader import load_json, save_json

router = Router()

BASE_DIR = Path(__file__).resolve().parent.parent
LEADS_PATH = BASE_DIR / "data" / "leads.json"


def _is_admin(user_id: int, settings: Settings) -> bool:
    return user_id in set(settings.admin_ids)


def _fmt_lead(i: int, lead: dict) -> str:
    ts = (lead.get("ts") or "—")
    user_id = lead.get("user_id")
    username = lead.get("username")
    name = (lead.get("name") or "").strip()
    contact_text = (lead.get("contact_text") or "").strip()

    who = []
    if name:
        who.append(name)
    if username:
        who.append(f"@{username}")
    if user_id:
        who.append(f"id:{user_id}")

    who_str = " | ".join(who) if who else "—"

    # ограничим длину, чтобы не улетать в лимиты Telegram
    if len(contact_text) > 700:
        contact_text = contact_text[:699].rstrip() + "…"

    return (
        f"<b>{i})</b> <i>{ts}</i>\n"
        f"<b>Кто:</b> {who_str}\n"
        f"<b>Контакт:</b> {contact_text}\n"
    )


@router.message(Command("list_leads"))
async def list_leads(message: types.Message, settings: Settings) -> None:
    """
    /list_leads — показывает последние 10 заявок
    /list_leads 20 — последние 20
    """
    if not _is_admin(message.from_user.id, settings):
        return

    args = (message.text or "").split(maxsplit=1)
    limit = 10
    if len(args) == 2:
        try:
            limit = max(1, min(50, int(args[1].strip())))
        except ValueError:
            limit = 10

    data = load_json(LEADS_PATH)
    if not isinstance(data, list) or not data:
        await message.answer("Пока нет заявок (leads.json пуст).")
        return

    last = list(reversed(data))[:limit]  # последние N
    blocks = []
    for idx, lead in enumerate(last, start=1):
        blocks.append(_fmt_lead(idx, lead))

    text = "<b>Последние заявки</b>\n\n" + "\n".join(blocks)
    await message.answer(text)


@router.message(Command("clear_leads"))
async def clear_leads(message: types.Message, settings: Settings) -> None:
    """
    /clear_leads — очистить leads.json (осторожно)
    """
    if not _is_admin(message.from_user.id, settings):
        return

    save_json(LEADS_PATH, [])
    await message.answer("✅ Заявки очищены (leads.json теперь пуст).")
