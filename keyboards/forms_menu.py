from __future__ import annotations

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_lead_contact_kb() -> ReplyKeyboardMarkup:
    """
    Клавиатура для заявки: без request_contact (чтобы Telegram не пугал предупреждением).
    Пользователь пишет контакт/комментарий текстом.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✍Написать контакт")],
            [KeyboardButton(text="⬅️ В меню")],
        ],
        resize_keyboard=True,
        selective=True,
        input_field_placeholder="Телефон / @username / удобное время…",
    )
