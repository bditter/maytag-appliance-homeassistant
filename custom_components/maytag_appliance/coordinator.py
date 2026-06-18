"""Push coordinator for Maytag Appliance."""

from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import timedelta
from functools import partial
import logging
from typing import Any, Callable

from whirlpool.appliance import Appliance
from whirlpool.appliancesmanager import AppliancesManager
from whirlpool.auth import AccountLockedError, Auth

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class MaytagDataCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Bridge Whirlpool push events to Home Assistant coordinator entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        manager: AppliancesManager,
        auth: Auth,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )
        self.manager = manager
        self.auth = auth
        self.washer_ids = [appliance.said for appliance in manager.washers]
        self.dryer_ids = [appliance.said for appliance in manager.dryers]
        self.appliances: dict[str, Appliance] = {
            appliance.said: appliance
            for appliance in [*manager.washers, *manager.dryers]
        }
        self.update_count = 0
        self.last_update_time = None
        self.last_update_times = {said: None for said in self.appliances}
        self._appliance_callbacks: dict[str, Callable[[], None]] = {
            said: partial(self._handle_appliance_update, said)
            for said in self.appliances
        }

    async def async_start(self) -> None:
        """Register push callbacks and connect to the cloud event socket."""
        for said, appliance in self.appliances.items():
            appliance.register_attr_callback(self._appliance_callbacks[said])
        try:
            await self.manager.connect()
        except Exception:
            for said, appliance in self.appliances.items():
                appliance.unregister_attr_callback(self._appliance_callbacks[said])
            raise
        self._publish_current_data()

    async def async_shutdown(self) -> None:
        """Disconnect from push updates and unregister callbacks."""
        for said, appliance in self.appliances.items():
            appliance.unregister_attr_callback(self._appliance_callbacks[said])
        await self.manager.disconnect()

    @callback
    def _handle_appliance_update(self, said: str) -> None:
        """Publish a websocket or REST attribute update immediately."""
        self._publish_current_data(said)

    @callback
    def _publish_current_data(self, updated_said: str | None = None) -> None:
        """Copy library appliance data into coordinator state."""
        self.update_count += 1
        self.last_update_time = dt_util.now()
        if updated_said is None:
            self.last_update_times = {
                said: self.last_update_time for said in self.appliances
            }
        else:
            self.last_update_times[updated_said] = self.last_update_time
        self.async_set_updated_data(
            {
                said: deepcopy(appliance._data_dict)  # noqa: SLF001
                for said, appliance in self.appliances.items()
            }
        )

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Perform a five-minute REST fallback refresh."""
        try:
            results = await asyncio.gather(
                *(appliance.fetch_data() for appliance in self.appliances.values())
            )
        except AccountLockedError as err:
            raise ConfigEntryAuthFailed("The Maytag account is locked") from err
        if not all(results):
            if not self.auth.is_access_token_valid():
                raise ConfigEntryAuthFailed(
                    "The saved Maytag credentials were rejected"
                )
            raise UpdateFailed("Unable to refresh one or more Maytag appliances")
        return {
            said: deepcopy(appliance._data_dict)  # noqa: SLF001
            for said, appliance in self.appliances.items()
        }
