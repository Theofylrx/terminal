"""
HTTP Client for calling other services
Centralized HTTP client with error handling
"""

import logging
import httpx
from typing import Dict, Any, Optional

logger = logging.getLogger("auto-trading-engine.http_client")


class HTTPClient:
    """HTTP client for making requests to other services."""

    def __init__(self, base_url: str, service_name: str, timeout: int = 30):
        """
        Initialize HTTP client.

        Args:
            base_url: Base URL for the service
            service_name: Name of the service (for logging)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.service_name = service_name
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Make GET request.

        Args:
            endpoint: API endpoint (e.g., "/api/v1/quote")
            params: Query parameters

        Returns:
            Response JSON if successful, None otherwise
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(
                f"❌ {self.service_name} HTTP error: {e.response.status_code} - {endpoint}"
            )
            return None

        except httpx.RequestError as e:
            logger.error(f"❌ {self.service_name} request error: {e} - {endpoint}")
            return None

        except Exception as e:
            logger.error(f"❌ {self.service_name} unexpected error: {e} - {endpoint}")
            return None

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Make POST request.

        Args:
            endpoint: API endpoint
            data: Form data
            json_data: JSON data

        Returns:
            Response JSON if successful, None otherwise
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = await self.client.post(url, data=data, json=json_data)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(
                f"❌ {self.service_name} HTTP error: {e.response.status_code} - {endpoint}"
            )
            return None

        except httpx.RequestError as e:
            logger.error(f"❌ {self.service_name} request error: {e} - {endpoint}")
            return None

        except Exception as e:
            logger.error(f"❌ {self.service_name} unexpected error: {e} - {endpoint}")
            return None

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
