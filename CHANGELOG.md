# Changelog

## 1.2.1 - 2026-06-18

- Make the washer/dryer machine-state value authoritative for status.
- Evaluate Sensing, Drying, and other phase flags only while machine state is
  Running (`7`), preventing latched flags from overriding Ready or Setting.
- Keep door open/closed exclusively in the dedicated binary sensor instead of
  overriding the appliance status.
- Prefer later dryer phases when multiple cloud flags are active.

## 1.2.0 - 2026-06-18

- Discover Maytag washers and dryers automatically during GUI setup; appliance
  IDs are no longer required.
- Use the same pinned `whirlpool-sixth-sense` library as Home Assistant core
  for Maytag US authentication, appliance discovery, and websocket events.
- Update entities immediately from cloud-push callbacks.
- Retain a five-minute REST refresh as a fallback if a push event is missed.
- Migrate existing entries by removing their legacy washer/dryer ID lists.

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
