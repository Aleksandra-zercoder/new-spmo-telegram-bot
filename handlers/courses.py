from __future__ import annotations

from pathlib import Path
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.main_menu import get_main_menu
from utils.json_loader import load_json

router = Router()

BASE_DIR = Path(__file__).resolve().parent.parent
COURSES_PATH = BASE_DIR / "data" / "courses.json"

# расширитель для "широкого" пузыря как в услугах (если понадобится)
WIDE_PAD = "⠀" * 60


def _load_courses() -> list[dict]:
    data = load_json(COURSES_PATH)
    if isinstance(data, dict) and isinstance(data.get("courses"), list):
        return data["courses"]
    if isinstance(data, list):
        return data
    return []


def _render_course(course: dict) -> str:
    name = (course.get("name") or course.get("title") or "").strip()
    short = (course.get("short") or "").strip()
    description = (course.get("description") or "").strip()

    lines = [f"<b>{name}</b>"]
    if short:
        lines += ["", short]
    if description:
        lines += ["", description]

    for field, title in [
        ("for_who", "Для кого"),
        ("benefits", "Преимущества"),
        ("program", "Программа"),
        ("results", "Что получите"),
    ]:
        items = course.get(field)
        if isinstance(items, list) and items:
            lines += ["", f"<b>{title}:</b>"]
            lines += [f"• {str(x).strip()}" for x in items if str(x).strip()]

    return "\n".join(lines)


def _courses_list_kb(courses: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for c in courses:
        cid = (c.get("id") or "").strip()
        name = (c.get("name") or c.get("title") or "").strip()
        if not cid or not name:
            continue
        rows.append([InlineKeyboardButton(text=name, callback_data=f"course:{cid}")])

    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="course:__menu__")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _lead_kb(course_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📩 Оставить заявку", callback_data=f"lead:course:{course_id}")],
        [InlineKeyboardButton(text="⬅️ К списку курсов", callback_data="course:__back__")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="course:__menu__")],
    ])


@router.message(F.text.contains("Курс") | F.text.contains("обуч"))
async def open_courses(message: types.Message) -> None:
    courses = _load_courses()
    if not courses:
        await message.answer("Пока нет опубликованных курсов.", reply_markup=get_main_menu())
        return

    await message.answer(
        f"Выберите курс:\n{WIDE_PAD}",
        reply_markup=_courses_list_kb(courses),
    )


@router.callback_query(F.data == "course:__menu__")
async def courses_to_menu(callback: types.CallbackQuery) -> None:
    await callback.message.answer("Главное меню 👇", reply_markup=get_main_menu())
    await callback.answer()


@router.callback_query(F.data == "course:__back__")
async def courses_back(callback: types.CallbackQuery) -> None:
    courses = _load_courses()
    if not courses:
        await callback.message.answer("Пока нет опубликованных курсов.", reply_markup=get_main_menu())
        await callback.answer()
        return

    await callback.message.answer(
        f"Выберите курс:\n{WIDE_PAD}",
        reply_markup=_courses_list_kb(courses),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("course:"))
async def show_course(callback: types.CallbackQuery) -> None:
    payload = callback.data.split("course:", 1)[1].strip()

    if payload in {"__menu__", "__back__"}:
        await callback.answer()
        return

    courses = _load_courses()
    course = next((c for c in courses if (c.get("id") or "").strip() == payload), None)

    await callback.answer()

    if not course:
        await callback.message.answer("Курс не найден.")
        return

    await callback.message.answer(_render_course(course), reply_markup=_lead_kb(payload))
