from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def _short_btn(text: str, max_len: int = 32) -> str:
    """
    Укорачивает подпись кнопки, чтобы не резалось некрасиво.
    Полное название всё равно будет в карточке услуги.
    """
    t = (text or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rstrip() + "…"


def build_services_root_kb() -> InlineKeyboardMarkup:
    """
    Ровно 2 кнопки: Аудиты / Сопровождение
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Аудиты", callback_data="svcgrp:audit")],
        [InlineKeyboardButton(text="Сопровождение", callback_data="svcgrp:support")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="svcgrp:menu")],
    ])


def build_services_list_kb(
    items: list[tuple[str, str]],
    *,
    back_cb: str = "svcgrp:back",
) -> InlineKeyboardMarkup:
    """
    Универсальный список услуг (inline, как у аудитов).
    items: [(service_id, service_name)]
    callback_data: svc:<service_id> (коротко и безопасно)
    """
    rows = []
    for service_id, name in items:
        rows.append([
            InlineKeyboardButton(
                text=_short_btn(name),
                callback_data=f"svc:{service_id}",
            )
        ])

    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=back_cb)])
    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="svcgrp:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
