"""Unit tests for bot handlers."""

from unittest.mock import AsyncMock, patch

import pytest
from aiogram.types import WebAppInfo

from bot.handlers import cmd_start


class TestCmdStart:
    async def test_sends_welcome_message(self):
        message = AsyncMock()

        with patch("bot.handlers.WEBAPP_URL", "https://example.com"):
            await cmd_start(message)

        message.answer.assert_awaited_once()
        call_args = message.answer.call_args
        text = call_args.args[0] if call_args.args else call_args.kwargs.get("text", "")
        assert "Welcome" in text

    async def test_includes_webapp_button(self):
        message = AsyncMock()

        with patch("bot.handlers.WEBAPP_URL", "https://example.com"):
            await cmd_start(message)

        call_kwargs = message.answer.call_args.kwargs
        markup = call_kwargs.get("reply_markup")
        assert markup is not None

        # Check inline keyboard has a WebApp button
        buttons = markup.inline_keyboard
        assert len(buttons) > 0
        button = buttons[0][0]
        assert button.web_app is not None
        assert button.web_app.url == "https://example.com"

    async def test_button_text(self):
        message = AsyncMock()

        with patch("bot.handlers.WEBAPP_URL", "https://example.com"):
            await cmd_start(message)

        markup = message.answer.call_args.kwargs["reply_markup"]
        button = markup.inline_keyboard[0][0]
        assert "Dating" in button.text or "Open" in button.text
