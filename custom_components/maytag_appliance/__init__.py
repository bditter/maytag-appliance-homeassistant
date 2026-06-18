"""The Maytag Appliance integration."""

from __future__ import annotations

from aiohttp import ClientError
from whirlpool.appliancesmanager import AppliancesManager
from whirlpool.auth import AccountLockedError, Auth
from whirlpool.backendselector import BackendSelector, Brand, Region

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import PLATFORMS
from .coordinator import MaytagDataCoordinator

LEGACY_CONFIG_KEYS = {"dryer_saids", "washer_saids"}


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Remove legacy manually configured appliance IDs."""
    if entry.version < 2:
        data = {
            key: value
            for key, value in entry.data.items()
            if key not in LEGACY_CONFIG_KEYS
        }
        hass.config_entries.async_update_entry(entry, data=data, version=2)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Maytag Appliance from a config entry."""
    session = async_get_clientsession(hass)
    backend = BackendSelector(Brand.Maytag, Region.US)
    auth = Auth(
        backend,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        session,
    )
    try:
        await auth.do_auth(store=False)
    except AccountLockedError as err:
        raise ConfigEntryAuthFailed("Maytag account is locked") from err
    except (ClientError, TimeoutError) as err:
        raise ConfigEntryNotReady("Unable to connect to Maytag service") from err

    if not auth.is_access_token_valid():
        raise ConfigEntryAuthFailed("Maytag credentials were rejected")

    manager = AppliancesManager(backend, auth, session)
    try:
        appliances_loaded = await manager.fetch_appliances()
    except (ClientError, TimeoutError) as err:
        raise ConfigEntryNotReady("Unable to discover Maytag appliances") from err
    if not appliances_loaded or (not manager.washers and not manager.dryers):
        raise ConfigEntryNotReady("No Maytag washer or dryer was discovered")

    coordinator = MaytagDataCoordinator(hass, entry, manager, auth)
    try:
        await coordinator.async_start()
    except AccountLockedError as err:
        raise ConfigEntryAuthFailed("Maytag account is locked") from err
    except (ClientError, TimeoutError) as err:
        raise ConfigEntryNotReady("Unable to start Maytag cloud updates") from err

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Maytag Appliance config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_shutdown()
    return unloaded
