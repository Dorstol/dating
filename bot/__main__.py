"""Entry point for the Telegram bot: python -m bot"""

import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config import BOT_TOKEN
from bot.handlers import router

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s:%(lineno)-3d %(levelname)-7s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is not set")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("Bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
