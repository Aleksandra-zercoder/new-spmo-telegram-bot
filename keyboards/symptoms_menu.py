from __future__ import annotations

import hashlib
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def _short_btn(text: str, max_len: int = 40) -> str:
    t = (text or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rstrip() + "…"


def cat_key(category: str) -> str:
    """
    Короткий безопасный ключ категории для callback_data (всегда ASCII и коротко).
    """
    return hashlib.md5(category.encode("utf-8")).hexdigest()[:8]


def build_symptoms_categories_kb(categories: list[str]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    for cat in categories:
        rows.append([
            InlineKeyboardButton(
                text=_short_btn(cat, 42),
                callback_data=f"symcat:{cat_key(cat)}",
            )
        ])

    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="symcat:__menu__")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_symptom_nav_kb(category: str, index: int, total: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    key = cat_key(category)

    nav_row: list[InlineKeyboardButton] = []
    if index > 0:
        nav_row.append(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"sym:item:{key}:{index - 1}",
            )
        )
    if index < total - 1:
        nav_row.append(
            InlineKeyboardButton(
                text="▶️ Далее",
                callback_data=f"sym:item:{key}:{index + 1}",
            )
        )
    if nav_row:
        rows.append(nav_row)

    rows.append([InlineKeyboardButton(text="Категории", callback_data="symcat:__back__")])
    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="symcat:__menu__")])

    return InlineKeyboardMarkup(inline_keyboard=rows)
