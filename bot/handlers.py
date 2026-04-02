from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import WEBAPP_URL

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start command — send WebApp button."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Open Dating App",
        web_app=WebAppInfo(url=WEBAPP_URL),
    )

    await message.answer(
        "Welcome to Dating App!\n\nTap the button below to open the app.",
        reply_markup=builder.as_markup(),
    )
