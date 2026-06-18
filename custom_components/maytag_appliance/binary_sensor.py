"""Binary sensors for Maytag appliances."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    APPLIANCE_DRYER,
    APPLIANCE_WASHER,
)
from .coordinator import MaytagDataCoordinator
from .entity import MaytagCoordinatorEntity, appliance_attribute, attribute_is_on


@dataclass(frozen=True, kw_only=True)
class MaytagBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describe a Maytag binary sensor."""

    attribute: str | None = None


WASHER_BINARY_SENSOR_DESCRIPTIONS = (
    MaytagBinarySensorEntityDescription(
        key="alert",
        name="Washer Alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alert-circle-outline",
    ),
    MaytagBinarySensorEntityDescription(
        key="online",
        name="Washer Online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        attribute="Online",
    ),
    MaytagBinarySensorEntityDescription(
        key="remote_enabled",
        name="Washer Remote Enabled",
        attribute="XCat_RemoteSetRemoteControlEnable",
        icon="mdi:remote",
    ),
    MaytagBinarySensorEntityDescription(
        key="door",
        name="Washer Door",
        device_class=BinarySensorDeviceClass.DOOR,
        attribute="Cavity_OpStatusDoorOpen",
    ),
    MaytagBinarySensorEntityDescription(
        key="door_locked",
        name="Washer Door Locked",
        attribute="Cavity_OpStatusDoorLocked",
        icon="mdi:lock",
    ),
    MaytagBinarySensorEntityDescription(
        key="need_clean",
        name="Washer Need Clean",
        device_class=BinarySensorDeviceClass.PROBLEM,
        attribute="WashCavity_CycleStatusCleanReminder",
        icon="mdi:washing-machine-alert",
    ),
)

DRYER_BINARY_SENSOR_DESCRIPTIONS = (
    MaytagBinarySensorEntityDescription(
        key="online",
        name="Dryer Online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        attribute="Online",
    ),
    MaytagBinarySensorEntityDescription(
        key="remote_enabled",
        name="Dryer Remote Enabled",
        attribute="XCat_RemoteSetRemoteControlEnable",
        icon="mdi:remote",
    ),
    MaytagBinarySensorEntityDescription(
        key="door",
        name="Dryer Door",
        device_class=BinarySensorDeviceClass.DOOR,
        attribute="Cavity_OpStatusDoorOpen",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Maytag appliance binary sensors."""
    coordinator: MaytagDataCoordinator = entry.runtime_data
    entities: list[MaytagBinarySensor] = []
    for said in coordinator.washer_ids:
        entities.extend(
            MaytagBinarySensor(coordinator, said, APPLIANCE_WASHER, description)
            for description in WASHER_BINARY_SENSOR_DESCRIPTIONS
        )
    for said in coordinator.dryer_ids:
        entities.extend(
            MaytagBinarySensor(coordinator, said, APPLIANCE_DRYER, description)
            for description in DRYER_BINARY_SENSOR_DESCRIPTIONS
        )
    async_add_entities(entities)


class MaytagBinarySensor(MaytagCoordinatorEntity, BinarySensorEntity):
    """Represent a Maytag appliance binary state."""

    entity_description: MaytagBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: MaytagDataCoordinator,
        said: str,
        appliance_type: str,
        description: MaytagBinarySensorEntityDescription,
    ) -> None:
        """Initialize a Maytag binary sensor."""
        super().__init__(coordinator, said, appliance_type)
        self.entity_description = description
        self._attr_unique_id = f"{said}_{appliance_type}_{description.key}"
        self.entity_id = (
            f"binary_sensor.maytag_{appliance_type}_{said.lower()}_{description.key}"
        )

    @property
    def is_on(self) -> bool | None:
        """Return the binary sensor state."""
        if self.entity_description.key == "alert":
            return self._washer_alert()
        if self.entity_description.attribute is None:
            return None
        return attribute_is_on(self.appliance_data, self.entity_description.attribute)

    def _washer_alert(self) -> bool | None:
        """Return whether the washer currently requires attention."""
        data = self.appliance_data
        if not data:
            return None
        return any(
            (
                attribute_is_on(data, "WashCavity_CycleStatusAddGarment"),
                attribute_is_on(data, "WashCavity_CycleStatusCleanReminder"),
                attribute_is_on(data, "Cavity_OpStatusDoorOpen"),
                str(appliance_attribute(data, "Online")) == "0",
            )
        )
