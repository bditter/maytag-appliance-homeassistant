"""Constants for the Whirlpool Appliance integration."""

DOMAIN = "whirlpool_appliance"

CONF_DRYER_SAIDS = "dryer_saids"
CONF_WASHER_SAIDS = "washer_saids"

APPLIANCE_DRYER = "dryer"
APPLIANCE_WASHER = "washer"

PLATFORMS = ["sensor"]

API_BASE_URL = "https://api.whrcloud.com"
API_CLIENT_ID = "maytag_android_v1"
API_CLIENT_SECRET = "f1XfYji_D9KfZGovyp8PMgRzrFKjhjY26TV0hu3Mt1-tCCNPl9s95z7QLUfB9UgB"

API_HEADERS = {
    "user-agent": "okhttp/4.12.0",
}
