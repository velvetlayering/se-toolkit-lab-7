"""
LMS Telegram Bot entry point.

Supports two modes:
1. --test mode: calls handlers directly, prints to stdout
2. Normal mode: runs Telegram bot (requires BOT_TOKEN)
"""

import sys
import asyncio

from handlers import ASYNC_COMMAND_HANDLERS, SYNC_COMMAND_HANDLERS
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


async def run_telegram_bot() -> None:
    """Run the Telegram bot (requires BOT_TOKEN)."""
    from config import load_config, get_bot_token
    from aiogram import Bot, Dispatcher, types
    from aiogram.filters import Command

    load_config()
    token = get_bot_token()

    if not token:
        print("Error: BOT_TOKEN not set. Please configure .env.bot.secret")
        return

    bot = Bot(token=token)
    dp = Dispatcher()

    # Register command handlers
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        from handlers import handle_start
        response = handle_start("/start")
        await message.answer(response)

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

    # Start polling
    print(f"Bot started. Polling for messages...")
    await dp.start_polling(bot)


def run_test_mode(command: str) -> None:
    """
    Run a command in test mode - print response to stdout.

    Args:
        command: The command to test (e.g., "/start", "/help")
    """
    response = asyncio.run(process_command_async(command))
    print(response)


def main() -> None:
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        if len(sys.argv) < 3:
            print("Usage: bot.py --test <command>")
            print("Example: bot.py --test \"/start\"")
            sys.exit(1)
        command = sys.argv[2]
        run_test_mode(command)
        sys.exit(0)
    else:
        # Normal mode: run Telegram bot
        asyncio.run(run_telegram_bot())


if __name__ == "__main__":
    main()
