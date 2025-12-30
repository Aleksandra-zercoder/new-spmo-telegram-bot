from __future__ import annotations

import hashlib
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def _short(text: str, max_len: int = 42) -> str:
    t = (text or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rstrip() + "…"


def cat_key(category: str) -> str:
    return hashlib.md5(category.encode("utf-8")).hexdigest()[:10]


def build_admin_categories_kb(categories: list[str]) -> InlineKeyboardMarkup:
    """
    Категории для /add_symptom: выбираем кнопку, чтобы не ошибиться.
    """
    rows: list[list[InlineKeyboardButton]] = []
    for cat in categories:
        rows.append([
            InlineKeyboardButton(
                text=_short(cat),
                callback_data=f"adm_symcat:{cat_key(cat)}",
            )
        ])

    rows.append([InlineKeyboardButton(text="➕ Новая категория", callback_data="adm_symnew")])
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="adm_symcancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_admin_del_categories_kb(categories: list[str]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for cat in categories:
        rows.append([
            InlineKeyboardButton(
                text=_short(cat),
                callback_data=f"adm_symdelcat:{cat_key(cat)}",
            )
        ])
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="adm_symcancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_admin_edit_categories_kb(categories: list[str]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for cat in categories:
        rows.append([
            InlineKeyboardButton(
                text=_short(cat),
                callback_data=f"adm_symeditcat:{cat_key(cat)}",
            )
        ])
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="adm_symcancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_admin_edit_field_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Заголовок", callback_data="adm_symentry:title")],
        [InlineKeyboardButton(text="Текст", callback_data="adm_symentry:text")],
        [InlineKeyboardButton(text="Отмена", callback_data="adm_symcancel")],
    ])
