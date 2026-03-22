"""
Command handlers for the LMS Telegram Bot.

Handlers are pure functions that take a command string and return a response.
They have no dependency on Telegram - same logic works from --test mode,
unit tests, or the Telegram bot.
"""

import asyncio
from typing import Callable, Awaitable

from services.api_client import LMSClient, create_lms_client


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


async def handle_health(user_input: str, client: LMSClient | None = None) -> str:
    """Handle /health command - checks backend status."""
    if client is None:
        client = create_lms_client()

    try:
        result = await client.health_check()
        return f"Backend is healthy. {result['item_count']} items available."
    except Exception as e:
        error_msg = str(e)
        # Extract meaningful error from exception
        if "Connection refused" in error_msg or "ConnectError" in error_msg:
            return f"Backend error: connection refused ({client.base_url}). Check that the services are running."
        elif "HTTP 502" in error_msg or "502 Bad Gateway" in error_msg:
            return f"Backend error: HTTP 502 Bad Gateway. The backend service may be down."
        elif "HTTP 401" in error_msg or "401 Unauthorized" in error_msg:
            return f"Backend error: HTTP 401 Unauthorized. Check your API key."
        else:
            return f"Backend error: {error_msg}. Check that the services are running."


async def handle_labs(user_input: str, client: LMSClient | None = None) -> str:
    """Handle /labs command - lists available labs."""
    if client is None:
        client = create_lms_client()

    try:
        items = await client.get_items()
        labs = [item for item in items if item.get("type") == "lab"]

        if not labs:
            return "No labs available."

        lines = ["Available labs:"]
        for lab in labs:
            lines.append(f"- {lab.get('title', 'Unknown')}")

        return "\n".join(lines)
    except Exception as e:
        error_msg = str(e)
        if "Connection refused" in error_msg or "ConnectError" in error_msg:
            return f"Backend error: connection refused ({client.base_url}). Check that the services are running."
        else:
            return f"Backend error: {error_msg}. Check that the services are running."


async def handle_scores(user_input: str, client: LMSClient | None = None) -> str:
    """Handle /scores command - returns scores for a lab."""
    if client is None:
        client = create_lms_client()

    # Extract lab name from command
    parts = user_input.split()
    if len(parts) < 2:
        return "Please specify a lab, e.g., /scores lab-04"

    lab = parts[1].lower()

    try:
        pass_rates = await client.get_pass_rates(lab)

        if not pass_rates:
            return f"No scores found for {lab}."

        # Format the lab name nicely
        lab_display = lab.replace("-", " ").title()
        lines = [f"Pass rates for {lab_display}:"]

        for rate in pass_rates:
            task_name = rate.get("task", rate.get("title", "Unknown"))
            percentage = rate.get("pass_rate", rate.get("percentage", 0))
            attempts = rate.get("attempts", 0)
            lines.append(f"- {task_name}: {percentage:.1f}% ({attempts} attempts)")

        return "\n".join(lines)
    except Exception as e:
        error_msg = str(e)
        if "Connection refused" in error_msg or "ConnectError" in error_msg:
            return f"Backend error: connection refused ({client.base_url}). Check that the services are running."
        elif "HTTP 404" in error_msg or "404 Not Found" in error_msg:
            return f"Lab not found: {lab}. Check the lab name."
        else:
            return f"Backend error: {error_msg}. Check that the services are running."


# Async command router: maps command names to async handler functions
ASYNC_COMMAND_HANDLERS: dict[str, Callable[[str, LMSClient | None], Awaitable[str]]] = {
    "/health": handle_health,
    "/labs": handle_labs,
    "/scores": handle_scores,
}

# Sync command router: maps command names to sync handler functions
SYNC_COMMAND_HANDLERS: dict[str, Callable[[str], str]] = {
    "/start": handle_start,
    "/help": handle_help,
}
