from __future__ import annotations

from pathlib import Path
from aiogram import Router, types, F

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
    """
    Находим реальную категорию по короткому ключу.
    """
    for c in categories:
        if cat_key(c) == key:
            return c
    return None


def _render_item(item: dict[str, str], *, index: int, total: int) -> str:
    title = (item.get("title") or "").strip()
    text = (item.get("text") or "").strip()
    header = f"({index + 1}/{total})"

    if title:
        return f"<b>{title}</b> {header}\n\n{text}"
    return f"{header}\n\n{text}" if text else f"{header}\n\n—"


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
        await callback.message.answer("Главное меню 👇", reply_markup=get_main_menu())
        await callback.answer()
        return

    if payload == "__back__":
        await callback.message.answer(
            "Выберите категорию:",
            reply_markup=build_symptoms_categories_kb(categories),
        )
        await callback.answer()
        return

    # payload теперь ключ (8 символов), а не текст категории
    category = _key_to_category(categories, payload)
    await callback.answer()

    if not category:
        await callback.message.answer("Категория не найдена. Откройте раздел заново.")
        return

    items = data.get(category, [])
    if not items:
        await callback.message.answer("В этой категории пока нет карточек.")
        return

    idx = 0
    total = len(items)
    msg = _render_item(items[idx], index=idx, total=total)

    await callback.message.answer(
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
    total = len(items)

    if total == 0 or idx < 0 or idx >= total:
        await callback.answer("Карточка не найдена")
        return

    msg = _render_item(items[idx], index=idx, total=total)

    await callback.answer()
    await callback.message.answer(
        msg,
        reply_markup=build_symptom_nav_kb(category, idx, total),
    )
