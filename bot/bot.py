"""
LMS Telegram Bot entry point.

Supports two modes:
1. --test mode: calls handlers directly, prints to stdout
2. Normal mode: runs Telegram bot (requires BOT_TOKEN)
"""

import sys
import asyncio

from handlers import COMMAND_HANDLERS


def process_command(command: str) -> str:
    """
    Route a command string to the appropriate handler.
    
    Args:
        command: The command string (e.g., "/start", "/scores lab-04")
    
    Returns:
        The handler's response text
    """
    # Extract the command name (first word)
    cmd_name = command.split()[0].lower()
    
    handler = COMMAND_HANDLERS.get(cmd_name)
    if handler:
        return handler(command)
    return f"Unknown command: {command}. Use /help for available commands."


async def run_telegram_bot() -> None:
    """Run the Telegram bot (requires BOT_TOKEN)."""
    # TODO: Implement Telegram bot startup
    print("Telegram bot mode not yet implemented")


def run_test_mode(command: str) -> None:
    """
    Run a command in test mode - print response to stdout.
    
    Args:
        command: The command to test (e.g., "/start", "/help")
    """
    response = process_command(command)
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
