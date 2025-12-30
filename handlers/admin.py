from __future__ import annotations

import json
from pathlib import Path
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import Settings
from utils.json_loader import load_json

router = Router()

BASE_DIR = Path(__file__).resolve().parent.parent
SYMPTOMS_PATH = BASE_DIR / "data" / "symptoms.json"


class AddSymptom(StatesGroup):
    category = State()
    title = State()
    text = State()


def _is_admin(user_id: int, settings: Settings) -> bool:
    return user_id in set(settings.admin_ids)


def _save_symptoms(data: dict) -> None:
    SYMPTOMS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SYMPTOMS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@router.message(Command("admin"))
async def admin_help(message: types.Message, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return

    await message.answer(
        "<b>Админ-панель</b>\n\n"
        "Команды:\n"
        "• /add_symptom — добавить карточку симптома\n"
        "• /cancel — отмена текущего действия\n"
    )


@router.message(Command("cancel"))
async def cancel_any(message: types.Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return
    await state.clear()
    await message.answer("Ок, отменено ✅")


@router.message(Command("add_symptom"))
async def add_symptom_start(message: types.Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return

    await state.clear()
    await state.set_state(AddSymptom.category)
    await message.answer(
        "Добавляем карточку в «Симптомы и решения».\n\n"
        "<b>Шаг 1/3</b>: напишите <b>название категории</b>\n"
        "Например: «Жвачка и ЖКТ»\n\n"
        "Отмена: /cancel"
    )


@router.message(AddSymptom.category)
async def add_symptom_category(message: types.Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return

    category = (message.text or "").strip()
    if not category:
        await message.answer("Категория не должна быть пустой. Напишите ещё раз.")
        return

    await state.update_data(category=category)
    await state.set_state(AddSymptom.title)
    await message.answer(
        "<b>Шаг 2/3</b>: напишите <b>заголовок карточки</b>\n"
        "Например: «Нет жвачки через 2 часа после кормления»\n\n"
        "Отмена: /cancel"
    )


@router.message(AddSymptom.title)
async def add_symptom_title(message: types.Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return

    title = (message.text or "").strip()
    if not title:
        await message.answer("Заголовок не должен быть пустым. Напишите ещё раз.")
        return

    await state.update_data(title=title)
    await state.set_state(AddSymptom.text)
    await message.answer(
        "<b>Шаг 3/3</b>: вставьте <b>текст карточки</b> (можно с буллетами)\n\n"
        "Отмена: /cancel"
    )


@router.message(AddSymptom.text)
async def add_symptom_text(message: types.Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return

    text = (message.text or "").strip()
    if not text:
        await message.answer("Текст не должен быть пустым. Напишите ещё раз.")
        return

    data_state = await state.get_data()
    await state.clear()

    category = data_state.get("category", "")
    title = data_state.get("title", "")

    data = load_json(SYMPTOMS_PATH)
    if not isinstance(data, dict):
        data = {}

    items = data.get(category)
    if not isinstance(items, list):
        items = []

    items.append({"title": title, "text": text})
    data[category] = items

    _save_symptoms(data)

    await message.answer(
        "✅ Карточка добавлена!\n\n"
        f"<b>Категория:</b> {category}\n"
        f"<b>Заголовок:</b> {title}\n"
        f"<b>Карточек в категории:</b> {len(items)}"
    )
