"""Constants for the Maytag Appliance integration."""

from homeassistant.const import Platform

DOMAIN = "maytag_appliance"

APPLIANCE_DRYER = "dryer"
APPLIANCE_WASHER = "washer"

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]
