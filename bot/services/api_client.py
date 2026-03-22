"""
LMS API Client.

Handles HTTP requests to the LMS backend with Bearer token authentication.
"""

import httpx
from typing import Any, Optional


class LMSClient:
    """Client for the LMS backend API."""

    def __init__(
        self,
        base_url: str = "http://localhost:42002",
        api_key: str = "",
    ):
        """
        Initialize the LMS client.

        Args:
            base_url: Base URL of the LMS backend
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    async def get_items(self) -> list[dict[str, Any]]:
        """
        Fetch all items (labs and tasks) from the backend.

        Returns:
            List of items with type, title, id, etc.

        Raises:
            httpx.HTTPError: If the request fails
        """
        url = f"{self.base_url}/items/"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._headers)
            response.raise_for_status()
            return response.json()

    async def get_pass_rates(self, lab: str) -> list[dict[str, Any]]:
        """
        Fetch pass rates for a specific lab.

        Args:
            lab: Lab identifier (e.g., "lab-04")

        Returns:
            List of pass rate data per task

        Raises:
            httpx.HTTPError: If the request fails
        """
        url = f"{self.base_url}/analytics/pass-rates"
        params = {"lab": lab}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._headers, params=params)
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> dict[str, Any]:
        """
        Check if the backend is healthy.

        Returns:
            Dict with status and item count

        Raises:
            httpx.HTTPError: If the request fails
        """
        items = await self.get_items()
        return {"status": "healthy", "item_count": len(items)}


def create_lms_client() -> LMSClient:
    """Create an LMS client from environment variables."""
    import os

    base_url = os.getenv("LMS_API_BASE_URL", "http://localhost:42002")
    api_key = os.getenv("LMS_API_KEY", "")

    return LMSClient(base_url=base_url, api_key=api_key)
