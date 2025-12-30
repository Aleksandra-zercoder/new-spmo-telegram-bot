from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import load_settings
from utils.loader import register_all_handlers

from handlers.digest_collector import router as digest_collector_router
from handlers.digest_admin import router as digest_admin_router


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = load_settings()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML")
    )

    dp = Dispatcher()
    dp["settings"] = settings

    dp.include_router(digest_collector_router)
    dp.include_router(digest_admin_router)

    register_all_handlers(dp)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
