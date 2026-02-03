from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import load_settings

# Пользовательские разделы
from handlers.start import router as start_router
from handlers.services import router as services_router
from handlers.courses import router as courses_router
from handlers.forms import router as forms_router
from handlers.symptoms import router as symptoms_router

# Админка / служебные
from handlers.admin import router as admin_router
from handlers.admin_symptoms import router as admin_symptoms_router
from handlers.leads_admin import router as leads_admin_router
from handlers.digest_admin import router as digest_admin_router
from handlers.digest_collector import router as digest_collector_router


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = load_settings()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    # ✅ чтобы хендлеры могли принимать settings: Settings
    dp.workflow_data.update(settings=settings)

    # ✅ порядок: старт → пользовательские разделы → формы → симптомы → служебные/админ
    dp.include_router(start_router)

    dp.include_router(services_router)
    dp.include_router(courses_router)
    dp.include_router(forms_router)
    dp.include_router(symptoms_router)

    # служебные/админские
    dp.include_router(digest_collector_router)
    dp.include_router(digest_admin_router)
    dp.include_router(leads_admin_router)
    dp.include_router(admin_symptoms_router)
    dp.include_router(admin_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
