from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def _short_btn(text: str, max_len: int = 48) -> str:
    """
    Укорачивает подпись кнопки, чтобы не резалось некрасиво.
    """
    t = (text or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rstrip() + "…"


def _course_btn_text(name: str, next_dates: str | None) -> str:
    """
    Формат подписи кнопки курса.
    Пример: "Курс по агрономии • 11–13 февраля 2026"
    """
    n = (name or "").strip()
    d = (next_dates or "").strip()
    if not d:
        return n
    return f"{n} • {d}"


def build_courses_list_kb(
    courses: list[dict],
    *,
    back_cb: str = "courses:menu",
    menu_cb: str = "main:menu",
) -> InlineKeyboardMarkup:
    """
    Список курсов (inline).
    callback_data: course:<course_id>
    Ожидаемые ключи в course: id, name, next_dates (опционально)
    """
    rows: list[list[InlineKeyboardButton]] = []

    for c in courses:
        course_id = str(c.get("id", "")).strip()
        name = str(c.get("name", "")).strip()
        next_dates = c.get("next_dates", "")

        if not course_id or not name:
            # пропускаем битые записи, чтобы не упал бот
            continue

        btn_text = _short_btn(_course_btn_text(name, str(next_dates)))
        rows.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"course:{course_id}",
            )
        ])

    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=back_cb)])
    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data=menu_cb)])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_courses_root_kb() -> InlineKeyboardMarkup:
    """
    Если у тебя есть "корневое" меню курсов (например: выбрать курс / календарь / FAQ),
    можешь использовать это. Если не нужно — можно удалить.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Выбрать курс", callback_data="courses:list")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="main:menu")],
    ])
