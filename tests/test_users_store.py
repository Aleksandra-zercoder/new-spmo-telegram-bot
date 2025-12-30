import json
from pathlib import Path

import pytest

import handlers.start as start_mod


def test_add_user_creates_file(monkeypatch, tmp_path: Path):
    users_path = tmp_path / "users.json"
    monkeypatch.setattr(start_mod, "USERS_PATH", users_path)

    start_mod.add_user(111)

    assert users_path.exists()
    data = json.loads(users_path.read_text(encoding="utf-8"))
    assert data["subscribers"] == [111]


def test_add_user_no_duplicates(monkeypatch, tmp_path: Path):
    users_path = tmp_path / "users.json"
    monkeypatch.setattr(start_mod, "USERS_PATH", users_path)

    start_mod.add_user(111)
    start_mod.add_user(111)
    start_mod.add_user(111)

    data = json.loads(users_path.read_text(encoding="utf-8"))
    assert data["subscribers"] == [111]


def test_add_user_sorts(monkeypatch, tmp_path: Path):
    users_path = tmp_path / "users.json"
    monkeypatch.setattr(start_mod, "USERS_PATH", users_path)

    start_mod.add_user(300)
    start_mod.add_user(100)
    start_mod.add_user(200)

    data = json.loads(users_path.read_text(encoding="utf-8"))
    assert data["subscribers"] == [100, 200, 300]
