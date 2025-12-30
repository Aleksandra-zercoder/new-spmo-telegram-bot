from __future__ import annotations

import json
from pathlib import Path

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import Settings
from utils.json_loader import load_json
from keyboards.admin_symptoms_menu import (
    build_admin_categories_kb,
    build_admin_del_categories_kb,
    build_admin_edit_categories_kb,
    build_admin_edit_field_kb,
    cat_key,
)

router = Router()

BASE_DIR = Path(__file__).resolve().parent.parent
SYMPTOMS_PATH = BASE_DIR / "data" / "symptoms.json"


class AddSymptom(StatesGroup):
    category = State()   # вводится только для НОВОЙ категории
    title = State()
    text = State()


class DelSymptom(StatesGroup):
    category = State()   # храним реальное имя категории
    index = State()


class EditSymptom(StatesGroup):
    category = State()   # реальное имя категории
    index = State()
    field = State()      # title/text
    new_value = State()


def _is_admin(user_id: int, settings: Settings) -> bool:
    return user_id in set(settings.admin_ids)


def _load_symptoms_dict() -> dict[str, list[dict[str, str]]]:
    data = load_json(SYMPTOMS_PATH)
    return data if isinstance(data, dict) else {}


def _save_symptoms(data: dict) -> None:
    SYMPTOMS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SYMPTOMS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _key_to_category(categories: list[str], key: str) -> str | None:
    for c in categories:
        if cat_key(c) == key:
            return c
    return None


def _format_categories_overview(data: dict[str, list[dict[str, str]]]) -> str:
    if not data:
        return "Пока нет категорий в symptoms.json"

    lines = ["<b>Категории «Симптомы и решения»</b>\n"]
    for cat in sorted(data.keys()):
        items = data.get(cat, [])
        cnt = len(items) if isinstance(items, list) else 0
        lines.append(f"• {cat} — <b>{cnt}</b>")
    return "\n".join(lines)


def _format_category_items(data: dict[str, list[dict[str, str]]], category: str, limit: int = 30) -> str:
    items = data.get(category, [])
    if not items:
        return f"В категории <b>{category}</b> пока нет карточек."

    lines = [f"<b>{category}</b>\n(показываю первые {min(len(items), limit)} из {len(items)})\n"]
    for i, item in enumerate(items[:limit], start=1):
        title = (item.get("title") or "").strip() or "— без заголовка —"
        lines.append(f"{i}. {title}")
    return "\n".join(lines)


@router.message(Command("admin"))
async def admin_help(message: types.Message, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return

    await message.answer(
        "<b>Админ-панель</b>\n\n"
        "Команды:\n"
        "• /add_symptom — добавить карточку\n"
        "• /list_symptoms — список категорий\n"
        "• /del_symptom — удалить карточку по номеру\n"
        "• /edit_symptom — редактировать заголовок/текст\n"
        "• /cancel — отмена\n"
    )


@router.message(Command("cancel"))
async def cancel_any(message: types.Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return
    await state.clear()
    await message.answer("Ок, отменено ✅")


@router.callback_query(F.data == "adm_symcancel")
async def cancel_any_cb(callback: types.CallbackQuery, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer()
        return
    await state.clear()
    await callback.answer("Отменено")
    await callback.message.answer("Ок, отменено ✅")


# -------------------------
# LIST
# -------------------------
@router.message(Command("list_symptoms"))
async def list_symptoms(message: types.Message, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return
    data = _load_symptoms_dict()
    await message.answer(_format_categories_overview(data))


# -------------------------
# ADD
# -------------------------
@router.message(Command("add_symptom"))
async def add_symptom_start(message: types.Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return

    await state.clear()
    data = _load_symptoms_dict()
    categories = sorted(data.keys())

    await message.answer(
        "Добавляем карточку в «Симптомы и решения».\n\n"
        "<b>Шаг 1/3</b>: выберите категорию кнопкой\n"
        "или нажмите «➕ Новая категория».\n\n"
        "Отмена: /cancel",
        reply_markup=build_admin_categories_kb(categories),
    )


@router.callback_query(F.data.startswith("adm_symcat:"))
async def add_symptom_pick_existing_category(callback: types.CallbackQuery, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer()
        return

    data = _load_symptoms_dict()
    categories = sorted(data.keys())

    key = (callback.data or "").split("adm_symcat:", 1)[-1].strip()
    category = _key_to_category(categories, key)

    if not category:
        await callback.answer("Категория не найдена")
        return

    await state.update_data(category=category)
    await state.set_state(AddSymptom.title)

    await callback.answer("Ок")
    await callback.message.answer(
        f"Категория: <b>{category}</b>\n\n"
        "<b>Шаг 2/3</b>: напишите <b>заголовок</b>\n\n"
        "Отмена: /cancel"
    )


@router.callback_query(F.data == "adm_symnew")
async def add_symptom_new_category(callback: types.CallbackQuery, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer()
        return

    await state.set_state(AddSymptom.category)
    await callback.answer("Ок")
    await callback.message.answer(
        "<b>Шаг 1/3</b>: напишите <b>название новой категории</b>\n"
        "Важно: если категория уже есть — выбирайте её кнопкой.\n\n"
        "Отмена: /cancel"
    )


@router.message(AddSymptom.category)
async def add_symptom_category_text(message: types.Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return

    category = (message.text or "").strip()
    if not category:
        await message.answer("Категория не должна быть пустой. Напишите ещё раз.")
        return

    await state.update_data(category=category)
    await state.set_state(AddSymptom.title)
    await message.answer(
        f"Категория: <b>{category}</b>\n\n"
        "<b>Шаг 2/3</b>: напишите <b>заголовок</b>\n\n"
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
        "<b>Шаг 3/3</b>: вставьте <b>текст карточки</b>\n\n"
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

    category = (data_state.get("category") or "").strip()
    title = (data_state.get("title") or "").strip()

    data = _load_symptoms_dict()
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


# -------------------------
# DELETE
# -------------------------
@router.message(Command("del_symptom"))
async def del_symptom_start(message: types.Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return

    await state.clear()
    data = _load_symptoms_dict()
    categories = sorted(data.keys())

    if not categories:
        await message.answer("Пока нет категорий для удаления.")
        return

    await message.answer(
        "Удаление карточки.\n\n"
        "<b>Шаг 1/2</b>: выберите категорию:",
        reply_markup=build_admin_del_categories_kb(categories),
    )


@router.callback_query(F.data.startswith("adm_symdelcat:"))
async def del_symptom_pick_category(callback: types.CallbackQuery, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer()
        return

    data = _load_symptoms_dict()
    categories = sorted(data.keys())

    key = (callback.data or "").split("adm_symdelcat:", 1)[-1].strip()
    category = _key_to_category(categories, key)

    if not category:
        await callback.answer("Категория не найдена")
        return

    items = data.get(category, [])
    if not items:
        await callback.answer()
        await callback.message.answer(f"В категории <b>{category}</b> пока нет карточек.")
        return

    await state.update_data(category=category)
    await state.set_state(DelSymptom.index)

    await callback.answer("Ок")
    await callback.message.answer(_format_category_items(data, category) + "\n\nОтправьте номер карточки для удаления.")


@router.message(DelSymptom.index)
async def del_symptom_by_index(message: types.Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return

    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Нужно отправить номер карточки (цифрой). Например: 2\n\nОтмена: /cancel")
        return

    idx = int(raw) - 1
    data_state = await state.get_data()
    category = (data_state.get("category") or "").strip()

    data = _load_symptoms_dict()
    items = data.get(category, [])

    if not items or idx < 0 or idx >= len(items):
        await message.answer("Такого номера нет. Отправьте номер из списка.\n\nОтмена: /cancel")
        return

    removed = items.pop(idx)
    data[category] = items
    _save_symptoms(data)

    await state.clear()

    removed_title = (removed.get("title") or "").strip() or "— без заголовка —"
    await message.answer(
        "🗑 Карточка удалена.\n\n"
        f"<b>Категория:</b> {category}\n"
        f"<b>Удалено:</b> {removed_title}\n"
        f"<b>Осталось в категории:</b> {len(items)}"
    )


# -------------------------
# EDIT (вариант А)
# -------------------------
@router.message(Command("edit_symptom"))
async def edit_symptom_start(message: types.Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return

    await state.clear()
    data = _load_symptoms_dict()
    categories = sorted(data.keys())

    if not categories:
        await message.answer("Пока нет категорий для редактирования.")
        return

    await message.answer(
        "Редактирование карточки.\n\n"
        "<b>Шаг 1/3</b>: выберите категорию:",
        reply_markup=build_admin_edit_categories_kb(categories),
    )


@router.callback_query(F.data.startswith("adm_symeditcat:"))
async def edit_symptom_pick_category(callback: types.CallbackQuery, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer()
        return

    data = _load_symptoms_dict()
    categories = sorted(data.keys())

    key = (callback.data or "").split("adm_symeditcat:", 1)[-1].strip()
    category = _key_to_category(categories, key)

    if not category:
        await callback.answer("Категория не найдена")
        return

    items = data.get(category, [])
    if not items:
        await callback.answer()
        await callback.message.answer(f"В категории <b>{category}</b> пока нет карточек.")
        return

    await state.update_data(category=category)
    await state.set_state(EditSymptom.index)

    await callback.answer("Ок")
    await callback.message.answer(
        _format_category_items(data, category) + "\n\n<b>Шаг 2/3</b>: отправьте номер карточки для редактирования."
    )


@router.message(EditSymptom.index)
async def edit_symptom_pick_index(message: types.Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return

    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Нужно отправить номер карточки (цифрой). Например: 3\n\nОтмена: /cancel")
        return

    idx = int(raw) - 1
    data_state = await state.get_data()
    category = (data_state.get("category") or "").strip()

    data = _load_symptoms_dict()
    items = data.get(category, [])

    if not items or idx < 0 or idx >= len(items):
        await message.answer("Такого номера нет. Отправьте номер из списка.\n\nОтмена: /cancel")
        return

    await state.update_data(index=idx)
    await state.set_state(EditSymptom.field)

    title = (items[idx].get("title") or "").strip() or "— без заголовка —"
    await message.answer(
        f"Выбрана карточка: <b>{title}</b>\n\n"
        "<b>Шаг 3/3</b>: что редактируем?",
        reply_markup=build_admin_edit_field_kb(),
    )


@router.callback_query(F.data.startswith("adm_symentry:"))
async def edit_symptom_pick_field(callback: types.CallbackQuery, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer()
        return

    field = (callback.data or "").split("adm_symentry:", 1)[-1].strip()
    if field not in ("title", "text"):
        await callback.answer("Неверный выбор")
        return

    await state.update_data(field=field)
    await state.set_state(EditSymptom.new_value)

    await callback.answer("Ок")
    await callback.message.answer("Отправьте новое значение.\n\nОтмена: /cancel")


@router.message(EditSymptom.new_value)
async def edit_symptom_apply(message: types.Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return

    new_value = (message.text or "").strip()
    if not new_value:
        await message.answer("Значение не должно быть пустым. Введите ещё раз.")
        return

    data_state = await state.get_data()
    category = (data_state.get("category") or "").strip()
    idx = int(data_state.get("index", -1))
    field = (data_state.get("field") or "").strip()

    data = _load_symptoms_dict()
    items = data.get(category, [])

    if not items or idx < 0 or idx >= len(items) or field not in ("title", "text"):
        await state.clear()
        await message.answer("Ошибка состояния. Начните заново: /edit_symptom")
        return

    old_value = (items[idx].get(field) or "").strip()
    items[idx][field] = new_value
    data[category] = items
    _save_symptoms(data)

    await state.clear()

    def _clip(s: str, n: int = 200) -> str:
        s = s or ""
        return s[:n] + ("…" if len(s) > n else "")

    await message.answer(
        "✅ Карточка обновлена!\n\n"
        f"<b>Категория:</b> {category}\n"
        f"<b>Поле:</b> {'Заголовок' if field == 'title' else 'Текст'}\n"
        f"<b>Было:</b> {_clip(old_value)}\n"
        f"<b>Стало:</b> {_clip(new_value)}"
    )
