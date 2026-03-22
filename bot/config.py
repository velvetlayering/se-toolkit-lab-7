"""
Configuration loading for the LMS Telegram Bot.

Loads secrets from environment variables, typically set via .env.bot.secret
"""

import os
from pathlib import Path
from dotenv import load_dotenv


def load_config() -> None:
    """
    Load configuration from .env.bot.secret file.
    
    This sets the following environment variables:
    - BOT_TOKEN: Telegram bot token
    - LMS_API_BASE_URL: Base URL for the LMS backend
    - LMS_API_KEY: API key for the LMS backend
    - LLM_API_KEY: API key for the LLM service
    - LLM_API_BASE_URL: Base URL for the LLM service
    """
    # Find the .env.bot.secret file in the bot directory
    bot_dir = Path(__file__).parent
    env_file = bot_dir / ".env.bot.secret"
    
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # Try parent directory (for when bot is run from repo root)
        env_file = bot_dir.parent / ".env.bot.secret"
        if env_file.exists():
            load_dotenv(env_file)


def get_bot_token() -> str:
    """Get the Telegram bot token."""
    return os.getenv("BOT_TOKEN", "")


def get_lms_api_base_url() -> str:
    """Get the LMS API base URL."""
    return os.getenv("LMS_API_BASE_URL", "http://localhost:42002")


def get_lms_api_key() -> str:
    """Get the LMS API key."""
    return os.getenv("LMS_API_KEY", "")


def get_llm_api_key() -> str:
    """Get the LLM API key."""
    return os.getenv("LLM_API_KEY", "")


def get_llm_api_base_url() -> str:
    """Get the LLM API base URL."""
    return os.getenv("LLM_API_BASE_URL", "")
