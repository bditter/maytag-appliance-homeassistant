"""Config flow for Maytag Appliance."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError
import voluptuous as vol
from whirlpool.appliancesmanager import AppliancesManager
from whirlpool.auth import AccountLockedError, Auth
from whirlpool.backendselector import BackendSelector, Brand, Region

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _user_schema() -> vol.Schema:
    """Build the initial setup schema without defaults."""
    return vol.Schema(
        {
            vol.Required(CONF_USERNAME): TextSelector(
                TextSelectorConfig(type=TextSelectorType.EMAIL)
            ),
            vol.Required(CONF_PASSWORD): TextSelector(
                TextSelectorConfig(type=TextSelectorType.PASSWORD)
            ),
        }
    )


def _reconfigure_schema(username: str) -> vol.Schema:
    """Build the reconfigure schema without displaying the saved password."""
    return vol.Schema(
        {
            vol.Required(CONF_USERNAME, default=username): TextSelector(
                TextSelectorConfig(type=TextSelectorType.EMAIL)
            ),
            vol.Optional(CONF_PASSWORD): TextSelector(
                TextSelectorConfig(type=TextSelectorType.PASSWORD)
            ),
        }
    )


async def _validate_input(hass, user_input: dict[str, Any]) -> dict[str, str]:
    """Validate credentials and confirm a washer or dryer is available."""
    data = {
        CONF_USERNAME: user_input[CONF_USERNAME].strip().lower(),
        CONF_PASSWORD: user_input[CONF_PASSWORD],
    }
    backend = BackendSelector(Brand.Maytag, Region.US)
    auth = Auth(
        backend,
        data[CONF_USERNAME],
        data[CONF_PASSWORD],
        async_get_clientsession(hass),
    )
    await auth.do_auth(store=False)
    if not auth.is_access_token_valid():
        raise InvalidCredentialsError

    manager = AppliancesManager(backend, auth, async_get_clientsession(hass))
    if not await manager.fetch_appliances() or (
        not manager.washers and not manager.dryers
    ):
        raise NoAppliancesError
    return data


class InvalidCredentialsError(Exception):
    """The Maytag credentials were rejected."""


class NoAppliancesError(Exception):
    """The account has no supported washer or dryer."""


class MaytagApplianceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Maytag Appliance."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle initial setup."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                data = await _validate_input(self.hass, user_input)
            except InvalidCredentialsError:
                errors["base"] = "invalid_auth"
            except AccountLockedError:
                errors["base"] = "account_locked"
            except NoAppliancesError:
                errors["base"] = "no_appliances"
            except (ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during Maytag setup")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(data[CONF_USERNAME])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=data[CONF_USERNAME], data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allow account credentials to be changed."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_PASSWORD):
                user_input[CONF_PASSWORD] = entry.data[CONF_PASSWORD]
            try:
                data = await _validate_input(self.hass, user_input)
            except InvalidCredentialsError:
                errors["base"] = "invalid_auth"
            except AccountLockedError:
                errors["base"] = "account_locked"
            except NoAppliancesError:
                errors["base"] = "no_appliances"
            except (ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during Maytag reconfiguration")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(data[CONF_USERNAME])
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    title=data[CONF_USERNAME],
                    data=data,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_reconfigure_schema((user_input or entry.data)[CONF_USERNAME]),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Start reauthentication."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Request a replacement password after authentication failure."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {**entry.data, CONF_PASSWORD: user_input[CONF_PASSWORD]}
            try:
                validated = await _validate_input(self.hass, data)
            except InvalidCredentialsError:
                errors["base"] = "invalid_auth"
            except AccountLockedError:
                errors["base"] = "account_locked"
            except NoAppliancesError:
                errors["base"] = "no_appliances"
            except (ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(entry, data=validated)

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    )
                }
            ),
            errors=errors,
        )
