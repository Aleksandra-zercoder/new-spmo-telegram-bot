import pytest

from keyboards.services_menu import build_services_root_kb, build_services_list_kb
from keyboards.courses_menu import build_courses_list_kb, build_courses_root_kb
from keyboards.symptoms_menu import (
    build_symptoms_categories_kb,
    build_symptom_nav_kb,
    cat_key as sym_cat_key,
)

from keyboards.admin_symptoms_menu import (
    cat_key as adm_cat_key,
    build_admin_categories_kb,
    build_admin_del_categories_kb,
    build_admin_edit_categories_kb,
    build_admin_edit_field_kb,
)


def _iter_inline_buttons(markup):
    # InlineKeyboardMarkup.inlne_keyboard -> list[list[InlineKeyboardButton]]
    for row in markup.inline_keyboard:
        for btn in row:
            yield btn


def _assert_callback_ok(markup):
    for btn in _iter_inline_buttons(markup):
        if btn.callback_data is None:
            continue
        # Telegram ограничивает callback_data 64 байтами
        assert len(btn.callback_data.encode("utf-8")) <= 64, f"callback_data too long: {btn.callback_data}"


def test_services_root_kb():
    kb = build_services_root_kb()
    assert kb.inline_keyboard, "Keyboard should have rows"
    _assert_callback_ok(kb)


def test_services_list_kb_callbacks():
    items = [
        ("audit_1", "Очень длинное название услуги, которое должно обрезаться красиво и не ломать кнопку"),
        ("audit_2", "Коротко"),
    ]
    kb = build_services_list_kb(items)
    _assert_callback_ok(kb)

    callbacks = [b.callback_data for b in _iter_inline_buttons(kb) if b.callback_data]
    assert "svc:audit_1" in callbacks
    assert "svc:audit_2" in callbacks


def test_courses_root_kb():
    kb = build_courses_root_kb()
    assert kb.inline_keyboard
    _assert_callback_ok(kb)


def test_courses_list_kb_includes_dates_in_text():
    courses = [
        {"id": "dpo_agronomy", "name": "Курс по агрономии", "next_dates": "11–13 февраля 2026"},
        {"id": "dpo_econ", "name": "Экономика поля и фермы", "next_dates": ""},
    ]
    kb = build_courses_list_kb(courses)
    _assert_callback_ok(kb)

    texts = [b.text for b in _iter_inline_buttons(kb)]
    assert any("11–13 февраля 2026" in t for t in texts), "Dates should appear in button text"
    assert any(t.startswith("Курс по агрономии") for t in texts)


def test_symptoms_categories_kb_callback_keys_short_ascii():
    categories = ["Жвачка и ЖКТ", "Маститы", "Отёлы"]
    kb = build_symptoms_categories_kb(categories)
    _assert_callback_ok(kb)

    # ключи всегда 8 hex символов
    for c in categories:
        k = sym_cat_key(c)
        assert len(k) == 8
        assert all(ch in "0123456789abcdef" for ch in k)


def test_symptoms_nav_kb_buttons_by_index():
    cat = "Жвачка и ЖКТ"
    total = 5

    kb_first = build_symptom_nav_kb(cat, index=0, total=total)
    texts_first = [b.text for b in _iter_inline_buttons(kb_first)]
    assert "◀️ Назад" not in texts_first
    assert "▶️ Далее" in texts_first

    kb_mid = build_symptom_nav_kb(cat, index=2, total=total)
    texts_mid = [b.text for b in _iter_inline_buttons(kb_mid)]
    assert "◀️ Назад" in texts_mid
    assert "▶️ Далее" in texts_mid

    kb_last = build_symptom_nav_kb(cat, index=total - 1, total=total)
    texts_last = [b.text for b in _iter_inline_buttons(kb_last)]
    assert "◀️ Назад" in texts_last
    assert "▶️ Далее" not in texts_last

    _assert_callback_ok(kb_first)
    _assert_callback_ok(kb_mid)
    _assert_callback_ok(kb_last)


def test_admin_symptoms_menus_callback_keys_short_ascii():
    categories = [
        "Жвачка и ЖКТ",
        "Очень-очень длинная категория симптомов, чтобы проверить обрезку и ключи",
    ]

    kb_add = build_admin_categories_kb(categories)
    kb_del = build_admin_del_categories_kb(categories)
    kb_edit = build_admin_edit_categories_kb(categories)

    _assert_callback_ok(kb_add)
    _assert_callback_ok(kb_del)
    _assert_callback_ok(kb_edit)

    # admin cat_key 10 hex символов
    for c in categories:
        k = adm_cat_key(c)
        assert len(k) == 10
        assert all(ch in "0123456789abcdef" for ch in k)


def test_admin_edit_field_kb_callbacks():
    kb = build_admin_edit_field_kb()
    _assert_callback_ok(kb)
    callbacks = [b.callback_data for b in _iter_inline_buttons(kb) if b.callback_data]
    assert "adm_symentry:title" in callbacks
    assert "adm_symentry:text" in callbacks
