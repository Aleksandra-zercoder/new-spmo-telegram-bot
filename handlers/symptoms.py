from __future__ import annotations

import html
from pathlib import Path

from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest

from keyboards.main_menu import get_main_menu
from keyboards.symptoms_menu import (
    build_symptoms_categories_kb,
    build_symptom_nav_kb,
    cat_key,
)
from utils.json_loader import load_json

router = Router()

BASE_DIR = Path(__file__).resolve().parent.parent
SYMPTOMS_PATH = BASE_DIR / "data" / "symptoms.json"


def _load_symptoms() -> dict[str, list[dict[str, str]]]:
    data = load_json(SYMPTOMS_PATH)
    return data if isinstance(data, dict) else {}


def _key_to_category(categories: list[str], key: str) -> str | None:
    """Находим реальную категорию по короткому ключу."""
    for c in categories:
        if cat_key(c) == key:
            return c
    return None


def _render_item(item: dict[str, str], *, index: int, total: int) -> str:
    # ✅ Экранируем HTML, чтобы не ломались сущности вроде "<30"
    title = html.escape((item.get("title") or "").strip())
    text = html.escape((item.get("text") or "").strip())

    header = f"({index + 1}/{total})"

    if title:
        return f"<b>{title}</b> {header}\n\n{text}"
    return f"{header}\n\n{text}" if text else f"{header}\n\n—"


async def _safe_edit_or_send(
    callback: types.CallbackQuery,
    text: str,
    reply_markup: types.InlineKeyboardMarkup | None = None,
) -> None:
    """
    Для навигации пытаемся редактировать сообщение.
    Если Telegram ругается (например message is not modified / can't be edited) —
    отправляем новое.
    """
    if not callback.message:
        return

    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=reply_markup)


@router.message(F.text.contains("Симптомы") & F.text.contains("решения"))
async def open_symptoms_menu(message: types.Message) -> None:
    data = _load_symptoms()
    categories = sorted(data.keys())

    if not categories:
        await message.answer(
            "Пока нет материалов в разделе «Симптомы и решения».",
            reply_markup=get_main_menu(),
        )
        return

    await message.answer(
        "Выберите категорию:",
        reply_markup=build_symptoms_categories_kb(categories),
    )


@router.callback_query(F.data.startswith("symcat:"))
async def on_symptoms_category(callback: types.CallbackQuery) -> None:
    data = _load_symptoms()
    categories = sorted(data.keys())

    payload = (callback.data or "").split("symcat:", 1)[-1]

    if payload == "__menu__":
        await callback.answer()
        if callback.message:
            await callback.message.answer("Главное меню 👇", reply_markup=get_main_menu())
        return

    if payload == "__back__":
        await callback.answer()
        await _safe_edit_or_send(
            callback,
            "Выберите категорию:",
            reply_markup=build_symptoms_categories_kb(categories),
        )
        return

    category = _key_to_category(categories, payload)
    if not category:
        await callback.answer("Категория не найдена")
        if callback.message:
            await callback.message.answer("Категория не найдена. Откройте раздел заново.")
        return

    items = data.get(category, [])
    if not isinstance(items, list) or not items:
        await callback.answer()
        if callback.message:
            await callback.message.answer("В этой категории пока нет карточек.")
        return

    idx = 0
    total = len(items)
    msg = _render_item(items[idx], index=idx, total=total)

    await callback.answer()
    await _safe_edit_or_send(
        callback,
        msg,
        reply_markup=build_symptom_nav_kb(category, idx, total),
    )


@router.callback_query(F.data.startswith("sym:item:"))
async def on_symptom_item(callback: types.CallbackQuery) -> None:
    data = _load_symptoms()
    categories = sorted(data.keys())

    payload = (callback.data or "").split("sym:item:", 1)[-1]

    try:
        cat_key_payload, index_str = payload.rsplit(":", 1)
        idx = int(index_str)
    except ValueError:
        await callback.answer("Ошибка навигации")
        return

    category = _key_to_category(categories, cat_key_payload)
    if not category:
        await callback.answer("Категория не найдена")
        return

    items = data.get(category, [])
    if not isinstance(items, list):
        await callback.answer("Ошибка данных категории")
        return

    total = len(items)
    if total == 0 or idx < 0 or idx >= total:
        await callback.answer("Карточка не найдена")
        return

    msg = _render_item(items[idx], index=idx, total=total)

    await callback.answer()
    await _safe_edit_or_send(
        callback,
        msg,
        reply_markup=build_symptom_nav_kb(category, idx, total),
    )
