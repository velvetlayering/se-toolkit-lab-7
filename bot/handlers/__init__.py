"""
Command handlers for the LMS Telegram Bot.

Handlers are pure functions that take a command string and return a response.
They have no dependency on Telegram - same logic works from --test mode,
unit tests, or the Telegram bot.
"""

from typing import Callable


def handle_start(user_input: str) -> str:
    """Handle /start command - returns welcome message."""
    return "Welcome to the LMS Bot! Use /help to see available commands."


def handle_help(user_input: str) -> str:
    """Handle /help command - lists available commands."""
    return "Available commands:\n/start - Welcome message\n/help - Show this help\n/health - Check backend status\n/labs - List available labs\n/scores <lab> - Get scores for a lab"


def handle_health(user_input: str) -> str:
    """Handle /health command - checks backend status."""
    return "Backend status: OK (placeholder)"


def handle_labs(user_input: str) -> str:
    """Handle /labs command - lists available labs."""
    return "Available labs: (placeholder)"


def handle_scores(user_input: str) -> str:
    """Handle /scores command - returns scores for a lab."""
    lab = user_input.replace("/scores", "").strip()
    if not lab:
        return "Please specify a lab, e.g., /scores lab-04"
    return f"Scores for {lab}: (placeholder)"


# Command router: maps command names to handler functions
COMMAND_HANDLERS: dict[str, Callable[[str], str]] = {
    "/start": handle_start,
    "/help": handle_help,
    "/health": handle_health,
    "/labs": handle_labs,
    "/scores": handle_scores,
}
