from __future__ import annotations

import json
from pathlib import Path

from aiogram import Router, types
from aiogram.filters import Command

from config import Settings
from utils.digest_publisher import build_digest_text, clear_store

router = Router()

BASE_DIR = Path(__file__).resolve().parent.parent
USERS_PATH = BASE_DIR / "data" / "users.json"


def _is_admin(user_id: int, settings: Settings) -> bool:
    return user_id in set(settings.admin_ids)


def _load_users() -> list[int]:
    if not USERS_PATH.exists():
        return []
    try:
        data = json.loads(USERS_PATH.read_text(encoding="utf-8"))
        return [int(x) for x in data.get("subscribers", [])]
    except Exception:
        return []


@router.message(Command("digest_status"))
async def digest_status(message: types.Message, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return

    users = _load_users()
    _, used = build_digest_text()

    await message.answer(
        f"👥 Пользователей (нажимали /start): <b>{len(users)}</b>\n"
        f"🗞 Пунктов в дайджесте за 7 дней: <b>{len(used)}</b>\n\n"
        "Команды:\n"
        "• /digest_preview — предпросмотр\n"
        "• /digest_broadcast — разослать всем\n"
        "• /digest_clear — очистить пункты дайджеста"
    )


@router.message(Command("digest_preview"))
async def digest_preview(message: types.Message, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return

    text, _ = build_digest_text()
    await message.answer("Предпросмотр (никому не отправляю):\n\n" + text)


@router.message(Command("digest_broadcast"))
async def digest_broadcast(message: types.Message, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return

    text, used = build_digest_text()
    user_ids = _load_users()

    if not user_ids:
        await message.answer("В users.json пока нет пользователей (никто не нажал /start).")
        return

    ok = 0
    bad = 0

    await message.answer(f"🚀 Начинаю рассылку. Получателей: {len(user_ids)}")

    for uid in user_ids:
        try:
            await message.bot.send_message(uid, text)
            ok += 1
        except Exception:
            bad += 1

    clear_store()

    await message.answer(
        f"✅ Готово.\n"
        f"Доставлено: {ok}\n"
        f"Ошибок: {bad}\n"
        f"Пунктов в дайджесте: {len(used)}\n"
        f"Хранилище очищено."
    )


@router.message(Command("digest_clear"))
async def digest_clear(message: types.Message, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return
    clear_store()
    await message.answer("🧹 Ок, пункты дайджеста очищены.")
