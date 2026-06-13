"""Data coordinator for Whirlpool Appliance."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    WhirlpoolApiClient,
    WhirlpoolApiError,
    WhirlpoolAuthenticationError,
    WhirlpoolConnectionError,
)
from .const import CONF_DRYER_SAIDS, CONF_WASHER_SAIDS, DOMAIN

_LOGGER = logging.getLogger(__name__)


class WhirlpoolDataCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Coordinate account authentication and appliance polling."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: WhirlpoolApiClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=2),
        )
        self.client = client
        self.update_count = 0
        self.appliance_ids = list(
            dict.fromkeys(
                entry.data.get(CONF_DRYER_SAIDS, [])
                + entry.data.get(CONF_WASHER_SAIDS, [])
            )
        )

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch all appliance data."""
        try:
            data = await self.client.async_get_appliances(self.appliance_ids)
            self.update_count += 1
            return data
        except WhirlpoolAuthenticationError as err:
            raise ConfigEntryAuthFailed(
                f"Authentication failed for {self.config_entry.data[CONF_USERNAME]}"
            ) from err
        except (WhirlpoolConnectionError, WhirlpoolApiError) as err:
            raise UpdateFailed(str(err)) from err
