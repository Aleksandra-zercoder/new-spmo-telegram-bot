from aiogram import Router, types
from aiogram.filters import Command
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
USERS_PATH = BASE_DIR / "data" / "users.json"

def _load_users() -> dict:
    if not USERS_PATH.exists():
        return {"subscribers": []}
    try:
        return json.loads(USERS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"subscribers": []}

def _save_users(data: dict) -> None:
    USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    USERS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def add_user(user_id: int) -> None:
    data = _load_users()
    subs = set(data.get("subscribers", []))
    subs.add(user_id)
    data["subscribers"] = sorted(subs)
    _save_users(data)

from keyboards.main_menu import get_main_menu

router = Router()

WELCOME_TEXT = (
    "Здравствуйте! \n\n"
    "Это бот Союза профессионалов молочной отрасли.\n\n"
    "Выберите раздел в меню ниже:"
)


@router.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    add_user(message.from_user.id)
    await message.answer(WELCOME_TEXT, reply_markup=get_main_menu())



@router.message(Command("menu"))
async def cmd_menu(message: types.Message) -> None:
    await message.answer("Главное меню", reply_markup=get_main_menu())


@router.message(lambda m: (m.text or "").strip() in {"⬅️ В меню", "В меню", "Меню"})
async def back_to_menu(message: types.Message) -> None:
    await message.answer("Главное меню", reply_markup=get_main_menu())
