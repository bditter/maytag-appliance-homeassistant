# Changelog

## 1.1.1 - 2026-06-14

- Refresh an expired Whirlpool access token automatically and retry appliance
  requests once.
- Only request Home Assistant reauthentication when the saved account
  credentials actually fail.

## 1.1.0 - 2026-06-13

- Rename the integration and domain to Maytag Appliance.
- Add dedicated washer alert, connectivity, control, door, cycle, cleaning,
  time remaining, and end-time entities.
- Add dedicated dryer connectivity, control, door, cycle, temperature, time
  remaining, and end-time entities.

## 1.0.0 - 2026-06-13

- Add the initial GUI-configured appliance integration.
- Add Home Assistant GUI setup and reconfiguration.
- Support updating account passwords and washer/dryer appliance IDs.
- Retain legacy Maytag entity IDs, states, and attributes.
- Add config-entry authentication recovery and coordinated cloud polling.
- Incorporate the upstream Whirlpool API header changes.
- Add HACS repository metadata and documentation.
