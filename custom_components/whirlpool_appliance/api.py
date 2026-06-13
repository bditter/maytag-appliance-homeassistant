"""Whirlpool cloud API client."""

from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import ClientResponseError, ClientSession

from .const import (
    API_BASE_URL,
    API_CLIENT_ID,
    API_CLIENT_SECRET,
    API_HEADERS,
)


class WhirlpoolApiError(Exception):
    """Base Whirlpool API error."""


class WhirlpoolAuthenticationError(WhirlpoolApiError):
    """Whirlpool authentication failed."""


class WhirlpoolConnectionError(WhirlpoolApiError):
    """Whirlpool cloud could not be reached."""


class WhirlpoolApiClient:
    """Client for the Whirlpool cloud API."""

    def __init__(self, session: ClientSession, username: str, password: str) -> None:
        """Initialize the API client."""
        self._session = session
        self._username = username
        self._password = password
        self._access_token: str | None = None

    async def async_authenticate(self) -> None:
        """Authenticate and retain an access token."""
        headers = {
            **API_HEADERS,
            "no_auth": "true",
            "content-type": "application/x-www-form-urlencoded",
        }
        data = {
            "client_id": API_CLIENT_ID,
            "client_secret": API_CLIENT_SECRET,
            "grant_type": "password",
            "username": self._username,
            "password": self._password,
        }

        try:
            response = await self._session.post(
                f"{API_BASE_URL}/oauth/token", data=data, headers=headers
            )
            if response.status in (400, 401, 403):
                raise WhirlpoolAuthenticationError("Invalid username or password")
            response.raise_for_status()
            payload = await response.json()
        except WhirlpoolAuthenticationError:
            raise
        except (ClientResponseError, TimeoutError, OSError) as err:
            raise WhirlpoolConnectionError("Unable to reach Whirlpool cloud") from err

        token = payload.get("access_token")
        if not token:
            raise WhirlpoolAuthenticationError(
                payload.get(
                    "error_description", "Authentication did not return a token"
                )
            )
        self._access_token = token

    async def async_get_appliance(self, said: str) -> dict[str, Any]:
        """Return data for one appliance."""
        if self._access_token is None:
            await self.async_authenticate()

        headers = {
            **API_HEADERS,
            "Authorization": f"bearer {self._access_token}",
        }
        try:
            response = await self._session.get(
                f"{API_BASE_URL}/api/v1/appliance/{said}", headers=headers
            )
            if response.status in (401, 403):
                raise WhirlpoolAuthenticationError("Whirlpool session expired")
            if response.status == 404:
                raise WhirlpoolApiError(f"Appliance ID {said} was not found")
            response.raise_for_status()
            return await response.json()
        except (WhirlpoolAuthenticationError, WhirlpoolApiError):
            raise
        except (ClientResponseError, TimeoutError, OSError) as err:
            raise WhirlpoolConnectionError("Unable to read appliance data") from err

    async def async_get_appliances(
        self, appliance_ids: list[str]
    ) -> dict[str, dict[str, Any]]:
        """Return data for all configured appliances."""
        if self._access_token is None:
            await self.async_authenticate()
        results = await asyncio.gather(
            *(self.async_get_appliance(said) for said in appliance_ids)
        )
        return dict(zip(appliance_ids, results, strict=True))
