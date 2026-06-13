"""Config flow for Maytag Appliance."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import (
    MaytagApiClient,
    MaytagApiError,
    MaytagAuthenticationError,
    MaytagConnectionError,
)
from .const import CONF_DRYER_SAIDS, CONF_WASHER_SAIDS, DOMAIN


def _parse_appliance_ids(value: str | list[str]) -> list[str]:
    """Parse appliance IDs from a comma- or line-separated value."""
    if isinstance(value, list):
        return value
    normalized = value.replace(",", "\n")
    return list(
        dict.fromkeys(
            item.strip().upper() for item in normalized.splitlines() if item.strip()
        )
    )


def _display_appliance_ids(value: list[str] | str) -> str:
    """Format stored appliance IDs for the form."""
    if isinstance(value, str):
        return value
    return "\n".join(value)


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
            vol.Optional(CONF_DRYER_SAIDS): TextSelector(
                TextSelectorConfig(multiline=True)
            ),
            vol.Optional(CONF_WASHER_SAIDS): TextSelector(
                TextSelectorConfig(multiline=True)
            ),
        }
    )


def _reconfigure_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Build the reconfigure schema without displaying the saved password."""
    return vol.Schema(
        {
            vol.Required(CONF_USERNAME, default=defaults[CONF_USERNAME]): TextSelector(
                TextSelectorConfig(type=TextSelectorType.EMAIL)
            ),
            vol.Optional(CONF_PASSWORD): TextSelector(
                TextSelectorConfig(type=TextSelectorType.PASSWORD)
            ),
            vol.Optional(
                CONF_DRYER_SAIDS,
                default=_display_appliance_ids(defaults.get(CONF_DRYER_SAIDS, [])),
            ): TextSelector(TextSelectorConfig(multiline=True)),
            vol.Optional(
                CONF_WASHER_SAIDS,
                default=_display_appliance_ids(defaults.get(CONF_WASHER_SAIDS, [])),
            ): TextSelector(TextSelectorConfig(multiline=True)),
        }
    )


async def _validate_input(hass, user_input: dict[str, Any]) -> dict[str, Any]:
    """Validate credentials and appliance IDs, returning normalized data."""
    data = {
        CONF_USERNAME: user_input[CONF_USERNAME].strip().lower(),
        CONF_PASSWORD: user_input[CONF_PASSWORD],
        CONF_DRYER_SAIDS: _parse_appliance_ids(user_input.get(CONF_DRYER_SAIDS, "")),
        CONF_WASHER_SAIDS: _parse_appliance_ids(user_input.get(CONF_WASHER_SAIDS, "")),
    }
    appliance_ids = list(
        dict.fromkeys(data[CONF_DRYER_SAIDS] + data[CONF_WASHER_SAIDS])
    )
    if not appliance_ids:
        raise ValueError("At least one appliance ID is required")

    client = MaytagApiClient(
        async_get_clientsession(hass),
        data[CONF_USERNAME],
        data[CONF_PASSWORD],
    )
    await client.async_authenticate()
    await client.async_get_appliances(appliance_ids)
    return data


class MaytagApplianceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Maytag Appliance."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle initial setup."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                data = await _validate_input(self.hass, user_input)
            except MaytagAuthenticationError:
                errors["base"] = "invalid_auth"
            except MaytagConnectionError:
                errors["base"] = "cannot_connect"
            except (MaytagApiError, ValueError):
                errors["base"] = "invalid_appliance"
            except Exception:  # noqa: BLE001
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
        """Allow account credentials and appliance IDs to be changed."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_PASSWORD):
                user_input[CONF_PASSWORD] = entry.data[CONF_PASSWORD]
            try:
                data = await _validate_input(self.hass, user_input)
            except MaytagAuthenticationError:
                errors["base"] = "invalid_auth"
            except MaytagConnectionError:
                errors["base"] = "cannot_connect"
            except (MaytagApiError, ValueError):
                errors["base"] = "invalid_appliance"
            except Exception:  # noqa: BLE001
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
            data_schema=_reconfigure_schema(user_input or dict(entry.data)),
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
                await _validate_input(self.hass, data)
            except MaytagAuthenticationError:
                errors["base"] = "invalid_auth"
            except MaytagConnectionError:
                errors["base"] = "cannot_connect"
            except (MaytagApiError, ValueError):
                errors["base"] = "invalid_appliance"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]},
                )

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
