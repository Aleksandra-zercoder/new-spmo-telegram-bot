from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu() -> ReplyKeyboardMarkup:
    """
    Компактное главное меню (2 колонки).
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Симптомы и решения"),
                KeyboardButton(text="Курсы и обучение"),
            ],
            [
                KeyboardButton(text="Аудит и сопровождение"),
                KeyboardButton(text="Оставить заявку"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел…",
        selective=True,
    )
