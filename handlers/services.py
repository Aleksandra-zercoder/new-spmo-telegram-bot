from __future__ import annotations

from pathlib import Path
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.main_menu import get_main_menu
from keyboards.services_menu import build_services_root_kb, build_services_list_kb
from utils.json_loader import load_json

router = Router()

BASE_DIR = Path(__file__).resolve().parent.parent
SERVICES_PATH = BASE_DIR / "data" / "services.json"

# "невидимый" расширитель строки (символ Брайля U+2800)
WIDE_PAD = "⠀" * 60


def _load_services() -> list[dict]:
    data = load_json(SERVICES_PATH)
    if isinstance(data, dict) and isinstance(data.get("services"), list):
        return data["services"]
    return []


def _services_by_group(group: str) -> list[dict]:
    services = _load_services()
    return [s for s in services if (s.get("group") or "").strip() == group]


def _render_service(service: dict) -> str:
    name = (service.get("name") or "").strip()
    short = (service.get("short") or "").strip()
    description = (service.get("description") or "").strip()

    lines = [f"<b>{name}</b>"]
    if short:
        lines += ["", short]
    if description:
        lines += ["", description]

    for field, title in [
        ("tasks_solved", "Решает задачи"),
        ("includes", "Что входит"),
        ("results", "Результат"),
    ]:
        items = service.get(field)
        if isinstance(items, list) and items:
            lines += ["", f"<b>{title}:</b>"]
            lines += [f"• {str(x).strip()}" for x in items if str(x).strip()]

    return "\n".join(lines)


def _support_sort_key(svc: dict) -> tuple:
    # Комплексное сопровождение всегда первым
    return (0 if (svc.get("id") == "support_complex") else 1, (svc.get("name") or ""))


@router.message(F.text.contains("Аудит") & F.text.contains("сопровождение"))
async def open_services(message: types.Message) -> None:
    await message.answer("Выберите направление:", reply_markup=build_services_root_kb())


@router.callback_query(F.data == "svcgrp:menu")
async def services_to_menu(callback: types.CallbackQuery) -> None:
    await callback.message.answer("Главное меню 👇", reply_markup=get_main_menu())
    await callback.answer()


@router.callback_query(F.data == "svcgrp:back")
async def services_back(callback: types.CallbackQuery) -> None:
    await callback.message.answer("Выберите направление:", reply_markup=build_services_root_kb())
    await callback.answer()


@router.callback_query(F.data == "svcgrp:audit")
async def open_audits(callback: types.CallbackQuery) -> None:
    audits = _services_by_group("audit")
    audits = sorted(audits, key=lambda s: (s.get("name") or ""))

    items = [
        ((s.get("id") or "").strip(), (s.get("name") or "").strip())
        for s in audits
        if (s.get("id") or "").strip() and (s.get("name") or "").strip()
    ]

    await callback.answer()

    if not items:
        await callback.message.answer("В разделе «Аудиты» пока нет услуг.")
        return

    await callback.message.answer(
        "Выберите аудит:",
        reply_markup=build_services_list_kb(items),
    )


@router.callback_query(F.data == "svcgrp:support")
async def open_support(callback: types.CallbackQuery) -> None:
    support = _services_by_group("specialized_service")
    support = sorted(support, key=_support_sort_key)

    items = [
        ((s.get("id") or "").strip(), (s.get("name") or "").strip())
        for s in support
        if (s.get("id") or "").strip() and (s.get("name") or "").strip()
    ]

    await callback.answer()

    if not items:
        await callback.message.answer("В разделе «Сопровождение» пока нет услуг.")
        return

    # ⬇️ расширяем пузырь, чтобы кнопки были как у аудитов
    text = f"Выберите формат сопровождения:\n{WIDE_PAD}"

    await callback.message.answer(
        text,
        reply_markup=build_services_list_kb(items),
    )


@router.callback_query(F.data.startswith("svc:"))
async def show_service(callback: types.CallbackQuery) -> None:
    service_id = callback.data.split("svc:", 1)[1]
    services = _load_services()
    service = next((s for s in services if (s.get("id") or "").strip() == service_id), None)

    await callback.answer()

    if not service:
        await callback.message.answer("Услуга не найдена.")
        return

    # 1️⃣ карточка услуги
    await callback.message.answer(_render_service(service))

    # 2️⃣ кнопка "Оставить заявку" с source = service:<id>
    lead_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📩 Оставить заявку",
                callback_data=f"lead:service:{service_id}",
            )
        ]
    ])

    await callback.message.answer(
        "Если хотите — оставьте заявку, мы свяжемся с вами.",
        reply_markup=lead_kb,
    )
