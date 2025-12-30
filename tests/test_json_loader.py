import json
from pathlib import Path

import pytest

from utils.json_loader import load_json, save_json


def test_load_json_missing_returns_empty_dict(tmp_path: Path):
    missing = tmp_path / "missing.json"
    data = load_json(missing)
    assert data == {}


def test_save_and_load_roundtrip(tmp_path: Path):
    p = tmp_path / "data.json"
    payload = {"a": 1, "b": [1, 2, 3], "c": {"x": "y"}}

    save_json(p, payload)
    loaded = load_json(p)

    assert loaded == payload
    assert p.exists()


def test_save_json_is_atomic(tmp_path: Path):
    p = tmp_path / "data.json"
    payload = {"ok": True}

    save_json(p, payload)

    # tmp-файл не должен остаться после replace
    tmp = p.with_suffix(p.suffix + ".tmp")
    assert not tmp.exists()
    assert json.loads(p.read_text(encoding="utf-8")) == payload


def test_load_json_invalid_raises(tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(Exception):
        load_json(p)
