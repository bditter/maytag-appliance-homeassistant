"""Status sensors for Maytag appliances."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    APPLIANCE_DRYER,
    APPLIANCE_WASHER,
    CONF_DRYER_SAIDS,
    CONF_WASHER_SAIDS,
    DOMAIN,
)
from .coordinator import MaytagDataCoordinator

UNIT_STATES = {
    "0": "Ready",
    "1": "Setting",
    "6": "Paused",
    "7": "Running",
    "8": "Wrinkle Prevent",
    "10": "Complete",
}

DRYER_CYCLES = {
    "1": "Regular",
    "2": "Heavy Duty",
    "4": "Delicates",
    "5": "Wrinkle Control",
    "6": "Bulky Items",
    "7": "Quick Dry",
    "11": "Timed Dry",
    "15": "Towels",
    "16": "Whites",
    "41": "Normal",
}
WASHER_CYCLES = {
    "1": "Normal/Regular",
    "2": "Heavy Duty",
    "4": "Quick Wash",
    "5": "Delicates",
    "8": "Drain & Spin",
    "10": "Whites",
    "11": "Towels",
    "16": "Wrinkle Control",
    "20": "Clean Wash",
    "22": "Bulky Items",
}
DRYER_TEMPERATURES = {
    "0": "Air Only",
    "2": "Low",
    "5": "Medium",
    "6": "Medium-High",
    "8": "High",
}
WASHER_TEMPERATURES = {
    "0": "Cold",
    "1": "Cool",
    "2": "Warm",
    "3": "Hot",
    "5": "Tap Cold",
}
SPIN_SPEEDS = {"0": "Off", "3": "Medium", "4": "Fast"}
SOIL_LEVELS = {
    "0": "Light",
    "1": "Normal",
    "2": "Heavy",
    "3": "Extra Heavy",
    "4": "Extra Light",
}
DRYNESS_LEVELS = {"1": "Less", "4": "Normal", "7": "More"}
STATUS_NAMES = {
    APPLIANCE_WASHER: "Washer Status",
    APPLIANCE_DRYER: "Dryer Status",
}


def _attribute(data: dict[str, Any], key: str) -> Any:
    """Safely read a Whirlpool appliance attribute value."""
    return data.get("attributes", {}).get(key, {}).get("value")


def _mapped(value: Any, values: dict[str, str]) -> Any:
    """Map a cloud value to a display value."""
    return values.get(str(value), value)


def _end_time(seconds: Any, base_time: datetime | None = None) -> datetime | None:
    """Calculate the estimated local end time."""
    try:
        return (base_time or dt_util.now()) + timedelta(seconds=int(seconds))
    except (TypeError, ValueError):
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Maytag appliance sensors."""
    coordinator: MaytagDataCoordinator = entry.runtime_data
    entities = [
        MaytagApplianceSensor(coordinator, said, APPLIANCE_DRYER)
        for said in entry.data.get(CONF_DRYER_SAIDS, [])
    ]
    for said in entry.data.get(CONF_DRYER_SAIDS, []):
        entities.extend(
            MaytagDetailSensor(coordinator, said, APPLIANCE_DRYER, description)
            for description in DRYER_SENSOR_DESCRIPTIONS
        )
    entities.extend(
        MaytagApplianceSensor(coordinator, said, APPLIANCE_WASHER)
        for said in entry.data.get(CONF_WASHER_SAIDS, [])
    )
    for said in entry.data.get(CONF_WASHER_SAIDS, []):
        entities.extend(
            MaytagDetailSensor(coordinator, said, APPLIANCE_WASHER, description)
            for description in WASHER_SENSOR_DESCRIPTIONS
        )
    async_add_entities(entities)


class MaytagApplianceSensor(CoordinatorEntity[MaytagDataCoordinator], SensorEntity):
    """Represent the status of a Maytag washer or dryer."""

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: MaytagDataCoordinator,
        said: str,
        appliance_type: str,
    ) -> None:
        """Initialize an appliance status sensor."""
        super().__init__(coordinator)
        self._said = said
        self._appliance_type = appliance_type
        self._attr_name = STATUS_NAMES[appliance_type]
        self._attr_unique_id = f"{said}_{appliance_type}_status"
        self.entity_id = f"sensor.maytag_{appliance_type}_{said.lower()}"

    @property
    def _data(self) -> dict[str, Any]:
        """Return this appliance's latest data."""
        return self.coordinator.data.get(self._said, {})

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information."""
        model = _attribute(self._data, "ModelNumber")
        serial = _attribute(self._data, "XCat_ApplianceInfoSetSerialNumber")
        device_name = f"Maytag {self._appliance_type.title()} {self._said[-4:]}"
        return DeviceInfo(
            identifiers={(DOMAIN, self._said)},
            manufacturer="Maytag",
            model=model,
            serial_number=serial,
            name=device_name,
        )

    @property
    def native_value(self) -> str:
        """Return the appliance's current status."""
        data = self._data
        state = _attribute(data, "Cavity_CycleStatusMachineState")
        if _attribute(data, "Cavity_OpStatusDoorOpen") == "1":
            return "Door Open"

        if self._appliance_type == APPLIANCE_DRYER:
            checks = (
                ("DryCavity_CycleStatusSensing", "Sensing", {"1", "true"}),
                ("DryCavity_CycleStatusDamp", "Damp", {"1", "true"}),
                ("DryCavity_CycleStatusDrying", "Drying", {"1", "true"}),
                ("DryCavity_CycleStatusSteaming", "Steaming", {"1", "true"}),
                ("DryCavity_CycleStatusCoolDown", "Cool Down", {"1", "true"}),
            )
        else:
            checks = (
                ("WashCavity_CycleStatusAddGarment", "Add Garmet", {"1", "true"}),
                ("WashCavity_CycleStatusSensing", "Sensing", {"1", "true"}),
                ("WashCavity_CycleStatusFilling", "Filling", {"1", "true"}),
                ("WashCavity_CycleStatusSoaking", "Soaking", {"1", "true"}),
                ("WashCavity_CycleStatusWashing", "Washing", {"1", "true"}),
                ("WashCavity_CycleStatusRinsing", "Rinsing", {"1", "true"}),
                ("WashCavity_CycleStatusDraining", "Draining", {"1", "true"}),
                ("WashCavity_CycleStatusSpinning", "Spinning", {"1", "true"}),
            )

        for key, label, active_values in checks:
            if str(_attribute(data, key)).lower() in active_values:
                return label
        return _mapped(state, UNIT_STATES) or "Unknown"

    @property
    def icon(self) -> str:
        """Return an icon reflecting appliance availability."""
        online = _attribute(self._data, "Online")
        if self._appliance_type == APPLIANCE_DRYER:
            return "mdi:tumble-dryer-off" if online == "0" else "mdi:tumble-dryer"
        if online == "0":
            return "mdi:washing-machine-off"
        if _attribute(self._data, "WashCavity_CycleStatusCleanReminder") == "1":
            return "mdi:washing-machine-alert"
        return "mdi:washing-machine"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return diagnostic and cycle attributes."""
        data = self._data
        remaining = _attribute(data, "Cavity_TimeStatusEstTimeRemaining")
        attributes = {
            "applianceid": data.get("applianceId", self._said),
            "modelNumber": _attribute(data, "ModelNumber"),
            "serialnumber": _attribute(data, "XCat_ApplianceInfoSetSerialNumber"),
            "lastsynced": data.get("lastFullSyncTime"),
            "lastmodified": data.get("lastModified"),
            "dooropen": _attribute(data, "Cavity_OpStatusDoorOpen"),
            "status": _attribute(data, "Cavity_CycleStatusMachineState"),
            "state": self.native_value,
            "statusnumber": _attribute(data, "Cavity_CycleStatusMachineState"),
            "operations": _attribute(data, "Cavity_OpSetOperations"),
            "poweronhours": _attribute(data, "XCat_OdometerStatusTotalHours"),
            "hoursinuse": _attribute(data, "XCat_OdometerStatusRunningHours"),
            "totalcycles": _attribute(data, "XCat_OdometerStatusCycleCount"),
            "remoteenabled": _attribute(data, "XCat_RemoteSetRemoteControlEnable"),
            "timeremaining": remaining,
            "end_time": _end_time(remaining, self.coordinator.last_update_time),
            "online": _attribute(data, "Online"),
        }

        if self._appliance_type == APPLIANCE_DRYER:
            cycle_id = _attribute(data, "DryCavity_CycleSetCycleSelect")
            attributes.update(
                {
                    "cycleid": cycle_id,
                    "cyclename": _mapped(cycle_id, DRYER_CYCLES),
                    "manualdrytime": _attribute(
                        data, "DryCavity_CycleSetManualDryTime"
                    ),
                    "drynesslevel": _mapped(
                        _attribute(data, "DryCavity_CycleSetDryness"),
                        DRYNESS_LEVELS,
                    ),
                    "temperature": _mapped(
                        _attribute(data, "DryCavity_CycleSetTemperature"),
                        DRYER_TEMPERATURES,
                    ),
                    "airflow": _attribute(data, "DryCavity_CycleStatusAirFlowStatus"),
                    "drying": _attribute(data, "DryCavity_CycleStatusDrying"),
                    "damp": _attribute(data, "DryCavity_CycleStatusDamp"),
                    "steaming": _attribute(data, "DryCavity_CycleStatusSteaming"),
                    "sensing": _attribute(data, "DryCavity_CycleStatusSensing"),
                    "cooldown": _attribute(data, "DryCavity_CycleStatusCoolDown"),
                    "reauth_cnt": 0,
                }
            )
        else:
            cycle_id = _attribute(data, "WashCavity_CycleSetCycleSelect")
            attributes.update(
                {
                    "cycleid": cycle_id,
                    "cyclename": _mapped(cycle_id, WASHER_CYCLES),
                    "doorlocked": _attribute(data, "Cavity_OpStatusDoorLocked"),
                    "draweropen": _attribute(
                        data, "WashCavity_OpStatusDispenserDrawerOpen"
                    ),
                    "needclean": _attribute(
                        data, "WashCavity_CycleStatusCleanReminder"
                    ),
                    "delaytime": _attribute(data, "Cavity_TimeSetDelayTime"),
                    "delayremaining": _attribute(
                        data, "Cavity_TimeStatusDelayTimeRemaining"
                    ),
                    "rinsing": _attribute(data, "WashCavity_CycleStatusRinsing"),
                    "draining": _attribute(data, "WashCavity_CycleStatusDraining"),
                    "filling": _attribute(data, "WashCavity_CycleStatusFilling"),
                    "spinning": _attribute(data, "WashCavity_CycleStatusSpinning"),
                    "soaking": _attribute(data, "WashCavity_CycleStatusSoaking"),
                    "sensing": _attribute(data, "WashCavity_CycleStatusSensing"),
                    "washing": _attribute(data, "WashCavity_CycleStatusWashing"),
                    "addgarmet": _attribute(data, "WashCavity_CycleStatusAddGarment"),
                    "temperature": _mapped(
                        _attribute(data, "WashCavity_CycleSetTemperature"),
                        WASHER_TEMPERATURES,
                    ),
                    "spinspeed": _mapped(
                        _attribute(data, "WashCavity_CycleSetSpinSpeed"),
                        SPIN_SPEEDS,
                    ),
                    "soillevel": _mapped(
                        _attribute(data, "WashCavity_CycleSetSoilLevel"),
                        SOIL_LEVELS,
                    ),
                    "dispense_enable": _attribute(
                        data, "WashCavity_CycleSetBulkDispense1Enable"
                    ),
                    "dispense_level": _attribute(
                        data, "WashCavity_OpStatusBulkDispense1Level"
                    ),
                    "dispense_concentration": _attribute(
                        data, "WashCavity_OpSetBulkDispense1Concentration"
                    ),
                    "auth_cnt": 0,
                    "update_count": self.coordinator.update_count,
                }
            )

        return attributes


WASHER_SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="cycle_id",
        name="Washer Cycle ID",
        icon="mdi:numeric",
    ),
    SensorEntityDescription(
        key="cycle_name",
        name="Washer Cycle Name",
        icon="mdi:washing-machine",
    ),
    SensorEntityDescription(
        key="time_remaining",
        name="Washer Time Remaining",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        icon="mdi:timer-outline",
    ),
    SensorEntityDescription(
        key="end_time",
        name="Washer End Time",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-end",
    ),
)

DRYER_SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="cycle_id",
        name="Dryer Cycle ID",
        icon="mdi:numeric",
    ),
    SensorEntityDescription(
        key="cycle_name",
        name="Dryer Cycle Name",
        icon="mdi:tumble-dryer",
    ),
    SensorEntityDescription(
        key="temperature",
        name="Dryer Temperature",
        icon="mdi:thermometer",
    ),
    SensorEntityDescription(
        key="time_remaining",
        name="Dryer Time Remaining",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        icon="mdi:timer-outline",
    ),
    SensorEntityDescription(
        key="end_time",
        name="Dryer End Time",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-end",
    ),
)


class MaytagDetailSensor(CoordinatorEntity[MaytagDataCoordinator], SensorEntity):
    """Represent one Maytag appliance detail as a dedicated sensor."""

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: MaytagDataCoordinator,
        said: str,
        appliance_type: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize a Maytag detail sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._said = said
        self._appliance_type = appliance_type
        self._attr_unique_id = f"{said}_{appliance_type}_{description.key}"
        self.entity_id = (
            f"sensor.maytag_{appliance_type}_{said.lower()}_{description.key}"
        )

    @property
    def _data(self) -> dict[str, Any]:
        """Return this appliance's latest data."""
        return self.coordinator.data.get(self._said, {})

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._said)},
            manufacturer="Maytag",
            model=_attribute(self._data, "ModelNumber"),
            serial_number=_attribute(self._data, "XCat_ApplianceInfoSetSerialNumber"),
            name=f"Maytag {self._appliance_type.title()} {self._said[-4:]}",
        )

    @property
    def native_value(self) -> Any:
        """Return the requested detail value."""
        key = self.entity_description.key
        data = self._data

        if key == "time_remaining":
            value = _attribute(data, "Cavity_TimeStatusEstTimeRemaining")
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
        if key == "end_time":
            return _end_time(
                _attribute(data, "Cavity_TimeStatusEstTimeRemaining"),
                self.coordinator.last_update_time,
            )

        if self._appliance_type == APPLIANCE_DRYER:
            cycle_id = _attribute(data, "DryCavity_CycleSetCycleSelect")
            if key == "cycle_id":
                return cycle_id
            if key == "cycle_name":
                return _mapped(cycle_id, DRYER_CYCLES)
            if key == "temperature":
                return _mapped(
                    _attribute(data, "DryCavity_CycleSetTemperature"),
                    DRYER_TEMPERATURES,
                )
        else:
            cycle_id = _attribute(data, "WashCavity_CycleSetCycleSelect")
            if key == "cycle_id":
                return cycle_id
            if key == "cycle_name":
                return _mapped(cycle_id, WASHER_CYCLES)

        return None
