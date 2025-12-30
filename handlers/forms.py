from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Any

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.main_menu import get_main_menu
from keyboards.forms_menu import get_lead_contact_kb
from config import Settings
from utils.json_loader import load_json, save_json  # ✅ НЕ ХВАТАЛО


router = Router()

BASE_DIR = Path(__file__).resolve().parent.parent
LEADS_PATH = BASE_DIR / "data" / "leads.json"


class LeadForm(StatesGroup):
    contact_text = State()


CONTACT_PROMPT = (
    "Чтобы мы могли связаться с вами и помочь 👇\n\n"
    "Напишите удобный способ связи (в любом виде):\n"
    "• номер телефона\n"
    "• Telegram: @username\n"
    "• или просто «Telegram»\n"
    "• можно добавить комментарий (удобное время, вопрос)\n\n"
    "Мы используем контакт только для связи по вашему запросу."
)


def _append_lead(entry: dict[str, Any]) -> None:
    data = load_json(LEADS_PATH)
    if not isinstance(data, list):
        data = []
    data.append(entry)
    save_json(LEADS_PATH, data)


def _is_menu_text(text: str) -> bool:
    t = (text or "").strip()
    return t in {"⬅️ В меню", "В меню", "Меню"}


def _is_lead_button(text: str) -> bool:
    t = (text or "").strip()
    # ловим и с эмодзи, и без
    return t in {"📩 Оставить заявку", "Оставить заявку"}


@router.message(F.text.func(_is_lead_button))
async def lead_start(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(LeadForm.contact_text)
    await message.answer(CONTACT_PROMPT, reply_markup=get_lead_contact_kb())


@router.message(LeadForm.contact_text)
async def lead_get_contact_text(message: types.Message, state: FSMContext, settings: Settings) -> None:
    text = (message.text or "").strip()

    if _is_menu_text(text):
        await state.clear()
        await message.answer("Главное меню", reply_markup=get_main_menu())
        return

    user = message.from_user

    _append_lead({
        "ts": datetime.now().isoformat(),
        "user_id": user.id,
        "username": user.username,
        "name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
        "contact_text": text,
    })

    # ✅ уведомление админу(ам) в личку
    who = []
    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    if name:
        who.append(name)
    if user.username:
        who.append(f"@{user.username}")
    who.append(f"id:{user.id}")

    admin_text = (
        "<b>📩 Новая заявка</b>\n\n"
        f"<b>Кто:</b> {' | '.join(who)}\n"
        f"<b>Контакт:</b> {text}"
    )

    for admin_id in settings.admin_ids:
        try:
            await message.bot.send_message(admin_id, admin_text)
        except Exception:
            # если админу нельзя написать (например, он не запускал бота) — не валим сценарий
            pass

    await state.clear()
    await message.answer(
        "Спасибо! Мы получили ваш контакт 👍\n\n"
        "Специалист СПМО свяжется с вами в ближайшее время.",
        reply_markup=get_main_menu(),
    )

