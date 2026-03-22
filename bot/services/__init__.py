"""
Services for the LMS Telegram Bot.

External API clients (LMS backend, LLM, etc.)
"""

from .api_client import LMSClient, create_lms_client

__all__ = ["LMSClient", "create_lms_client"]
