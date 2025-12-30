import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

MSK = timezone(timedelta(hours=3))


def test_build_digest_empty(monkeypatch, tmp_path):
    # импорт внутри теста, чтобы monkeypatch сработал
    import utils.digest_publisher as dp

    store = tmp_path / "weekly_digest_items.json"
    store.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(dp, "STORE_PATH", store)

    text, items = dp.build_digest_text()
    assert "Дайджест недели" in text
    assert "без публикаций" in text.lower()
    assert items == []


def test_build_digest_with_items(monkeypatch, tmp_path):
    import utils.digest_publisher as dp

    store = tmp_path / "weekly_digest_items.json"
    now = datetime.now(MSK)

    data = [
        {
            "ts": (now - timedelta(days=1)).isoformat(),
            "message_id": 10,
            "title": "Новость 1",
            "link": "https://t.me/unionpmo/10"
        },
        {
            "ts": (now - timedelta(days=2)).isoformat(),
            "message_id": 11,
            "title": "Новость 2",
            "link": "https://t.me/unionpmo/11"
        },
    ]
    store.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(dp, "STORE_PATH", store)

    text, items = dp.build_digest_text()
    assert "1) Новость 1" in text
    assert "https://t.me/unionpmo/10" in text
    assert len(items) == 2


def test_build_digest_filters_old(monkeypatch, tmp_path):
    import utils.digest_publisher as dp

    store = tmp_path / "weekly_digest_items.json"
    now = datetime.now(MSK)

    data = [
        {
            "ts": (now - timedelta(days=10)).isoformat(),  # слишком старое
            "message_id": 99,
            "title": "Старая новость",
            "link": "https://t.me/unionpmo/99"
        }
    ]
    store.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(dp, "STORE_PATH", store)

    text, items = dp.build_digest_text()
    assert items == []
    assert "без публикаций" in text.lower()


def test_clear_store(monkeypatch, tmp_path):
    import utils.digest_publisher as dp

    store = tmp_path / "weekly_digest_items.json"
    store.write_text('[{"x":1}]', encoding="utf-8")
    monkeypatch.setattr(dp, "STORE_PATH", store)

    dp.clear_store()
    assert store.read_text(encoding="utf-8").strip() == "[]"
