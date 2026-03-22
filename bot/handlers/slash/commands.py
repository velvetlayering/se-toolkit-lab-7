"""
Command handlers for slash commands.

These are plain functions separated from the Telegram transport layer.
"""


def handle_start(user_input: str) -> str:
    """Handle /start command - returns welcome message."""
    return "Welcome to the LMS Bot! Use /help to see available commands."


def handle_help(user_input: str) -> str:
    """Handle /help command - lists available commands."""
    return (
        "Available commands:\n"
        "/start - Welcome message\n"
        "/help - Show this help\n"
        "/health - Check backend status\n"
        "/labs - List available labs\n"
        "/scores <lab> - Get scores for a lab"
    )
