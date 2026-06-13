"""Shared entities for the Maytag Appliance integration."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MaytagDataCoordinator


def appliance_attribute(data: dict[str, Any], key: str) -> Any:
    """Safely read a Maytag appliance attribute value."""
    return data.get("attributes", {}).get(key, {}).get("value")


def attribute_is_on(data: dict[str, Any], key: str) -> bool | None:
    """Convert a cloud attribute to a binary state."""
    value = appliance_attribute(data, key)
    if value is None:
        return None
    return str(value).lower() in {"1", "true", "on", "yes"}


class MaytagCoordinatorEntity(CoordinatorEntity[MaytagDataCoordinator]):
    """Base entity attached to one Maytag appliance."""

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: MaytagDataCoordinator,
        said: str,
        appliance_type: str,
    ) -> None:
        """Initialize a Maytag appliance entity."""
        super().__init__(coordinator)
        self._said = said
        self._appliance_type = appliance_type

    @property
    def appliance_data(self) -> dict[str, Any]:
        """Return this appliance's latest data."""
        return self.coordinator.data.get(self._said, {})

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._said)},
            manufacturer="Maytag",
            model=appliance_attribute(self.appliance_data, "ModelNumber"),
            serial_number=appliance_attribute(
                self.appliance_data, "XCat_ApplianceInfoSetSerialNumber"
            ),
            name=f"Maytag {self._appliance_type.title()} {self._said[-4:]}",
        )
