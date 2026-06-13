"""Data coordinator for Maytag Appliance."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import (
    MaytagApiClient,
    MaytagApiError,
    MaytagAuthenticationError,
    MaytagConnectionError,
)
from .const import CONF_DRYER_SAIDS, CONF_WASHER_SAIDS, DOMAIN

_LOGGER = logging.getLogger(__name__)


class MaytagDataCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Coordinate account authentication and appliance polling."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: MaytagApiClient,
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
        self.last_update_time = None
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
            self.last_update_time = dt_util.now()
            return data
        except MaytagAuthenticationError as err:
            raise ConfigEntryAuthFailed(
                f"Authentication failed for {self.config_entry.data[CONF_USERNAME]}"
            ) from err
        except (MaytagConnectionError, MaytagApiError) as err:
            raise UpdateFailed(str(err)) from err
