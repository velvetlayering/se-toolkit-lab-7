"""
LMS Telegram Bot entry point.

Supports two modes:
1. --test mode: calls handlers directly, prints to stdout
2. Normal mode: runs Telegram bot (requires BOT_TOKEN)
"""

import sys
import asyncio

from handlers import ASYNC_COMMAND_HANDLERS, SYNC_COMMAND_HANDLERS
from handlers.intent_router import route_intent
from services.api_client import create_lms_client


async def process_command_async(command: str) -> str:
    """
    Route a command string to the appropriate async handler.

    Args:
        command: The command string (e.g., "/start", "/scores lab-04")

    Returns:
        The handler's response text
    """
    # Extract the command name (first word)
    cmd_name = command.split()[0].lower()

    # Check sync handlers first (no API calls needed)
    sync_handler = SYNC_COMMAND_HANDLERS.get(cmd_name)
    if sync_handler:
        return sync_handler(command)

    # Check async handlers (require API calls)
    async_handler = ASYNC_COMMAND_HANDLERS.get(cmd_name)
    if async_handler:
        client = create_lms_client()
        return await async_handler(command, client)

    return f"Unknown command: {command}. Use /help for available commands."


async def process_message_async(message: str, debug: bool = True) -> str:
    """
    Process a natural language message through the intent router.

    Args:
        message: The user's message (not a slash command)
        debug: If True, print debug info to stderr

    Returns:
        The bot's response
    """
    # Check if it's actually a command
    if message.strip().startswith("/"):
        return await process_command_async(message.strip())

    # Route through LLM
    return await route_intent(message, debug=debug)


async def run_telegram_bot() -> None:
    """Run the Telegram bot (requires BOT_TOKEN)."""
    from config import load_config, get_bot_token
    from aiogram import Bot, Dispatcher, types
    from aiogram.filters import Command
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    load_config()
    token = get_bot_token()

    if not token:
        print("Error: BOT_TOKEN not set. Please configure .env.bot.secret")
        return

    bot = Bot(token=token)
    dp = Dispatcher()

    # Inline keyboard buttons for common actions
    def get_main_keyboard() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="📚 Available Labs", callback_data="labs"),
                    InlineKeyboardButton(text="💚 Health Check", callback_data="health"),
                ],
                [
                    InlineKeyboardButton(text="📊 Scores", callback_data="scores"),
                    InlineKeyboardButton(text="❓ Help", callback_data="help"),
                ],
            ]
        )

    # Register command handlers
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        from handlers import handle_start
        response = handle_start("/start")
        await message.answer(response, reply_markup=get_main_keyboard())

    @dp.message(Command("help"))
    async def cmd_help(message: types.Message):
        from handlers import handle_help
        response = handle_help("/help")
        await message.answer(response)

    @dp.message(Command("health"))
    async def cmd_health(message: types.Message):
        response = await process_command_async("/health")
        await message.answer(response)

    @dp.message(Command("labs"))
    async def cmd_labs(message: types.Message):
        response = await process_command_async("/labs")
        await message.answer(response)

    @dp.message(Command("scores"))
    async def cmd_scores(message: types.Message):
        # Get the lab argument if provided
        lab_arg = message.text.replace("/scores", "").strip()
        command = f"/scores {lab_arg}" if lab_arg else "/scores"
        response = await process_command_async(command)
        await message.answer(response)

    # Handle callback queries from inline buttons
    @dp.callback_query()
    async def handle_callback(callback: types.CallbackQuery):
        action = callback.data

        if action == "labs":
            response = await process_command_async("/labs")
        elif action == "health":
            response = await process_command_async("/health")
        elif action == "scores":
            response = "Send me a lab name, e.g., 'lab-04' or ask 'show scores for lab 4'"
        elif action == "help":
            from handlers import handle_help
            response = handle_help("/help")
        else:
            response = "Unknown action."

        await callback.message.answer(response)
        await callback.answer()

    # Handle natural language messages
    @dp.message()
    async def handle_message(message: types.Message):
        if not message.text:
            return

        user_text = message.text.strip()
        response = await process_message_async(user_text, debug=True)
        await message.answer(response)

    # Start polling
    print(f"Bot started. Polling for messages...")
    await dp.start_polling(bot)


def run_test_mode(command: str) -> None:
    """
    Run a command in test mode - print response to stdout.

    Args:
        command: The command to test (e.g., "/start", "/help", or natural language)
    """
    # Check if it's a slash command or natural language
    if command.strip().startswith("/"):
        response = asyncio.run(process_command_async(command))
    else:
        response = asyncio.run(process_message_async(command, debug=True))
    print(response)


def main() -> None:
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        if len(sys.argv) < 3:
            print("Usage: bot.py --test <command>")
            print("Example: bot.py --test \"/start\"")
            print("Example: bot.py --test \"what labs are available\"")
            sys.exit(1)
        command = sys.argv[2]
        run_test_mode(command)
        sys.exit(0)
    else:
        # Normal mode: run Telegram bot
        asyncio.run(run_telegram_bot())


if __name__ == "__main__":
    main()
