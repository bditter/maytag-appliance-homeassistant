# Maytag Appliance for Home Assistant

<p align="center">
  <img src="custom_components/maytag_appliance/brand/logo@2x.png"
       alt="Maytag Appliance for Home Assistant"
       width="256">
</p>

[![GitHub Release](https://img.shields.io/github/v/release/bditter/maytag-appliance-homeassistant?style=for-the-badge)](https://github.com/bditter/maytag-appliance-homeassistant/releases)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5?style=for-the-badge&logo=home-assistant-community-store)](https://hacs.xyz/docs/faq/custom_repositories/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-18BCF2?style=for-the-badge&logo=home-assistant&logoColor=white)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/github/license/bditter/maytag-appliance-homeassistant?style=for-the-badge)](LICENSE.txt)

[![GitHub Stars](https://img.shields.io/github/stars/bditter/maytag-appliance-homeassistant?style=flat-square)](https://github.com/bditter/maytag-appliance-homeassistant/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/bditter/maytag-appliance-homeassistant?style=flat-square)](https://github.com/bditter/maytag-appliance-homeassistant/issues)
[![Last Commit](https://img.shields.io/github/last-commit/bditter/maytag-appliance-homeassistant?style=flat-square)](https://github.com/bditter/maytag-appliance-homeassistant/commits/main)

This custom integration provides status sensors for Maytag washers and dryers
using the Whirlpool cloud API. It supports Home Assistant GUI setup and does
not require YAML configuration.

## Features

- GUI setup through **Settings > Devices & services**.
- Automatic discovery of Maytag washers and dryers on the account.
- Editable account password through **Reconfigure**.
- Existing Maytag entity IDs and state attributes retained for compatibility.
- Dedicated entities for appliance status, connectivity, doors, cycles, and
  remaining time.
- Near-real-time cloud push updates with a five-minute REST fallback refresh.
- HACS custom repository support.

## Entities

### Washer

- Washer Alert
- Washer Online
- Washer Remote Enabled
- Washer Status
- Washer Door
- Washer Door Locked
- Washer Cycle ID
- Washer Cycle Name
- Washer Need Clean
- Washer Time Remaining
- Washer End Time

### Dryer

- Dryer Online
- Dryer Remote Enabled
- Dryer Status
- Dryer Door
- Dryer Cycle ID
- Dryer Cycle Name
- Dryer Temperature
- Dryer Time Remaining
- Dryer End Time

Online, remote-enabled, door, door-locked, need-clean, and alert values are
binary sensors. Status, cycle, temperature, and time values are sensors.

## Architecture

This is a standalone custom integration and does not import Home Assistant's
core Whirlpool integration. It directly pins the same maintained
`whirlpool-sixth-sense` library version used by core for Maytag US
authentication, discovery, REST fallback updates, and websocket events. Core
integration changes therefore do not alter this integration's entities or
configuration.

## Installation

### HACS

1. Open HACS and select **Integrations**.
2. Open the menu and choose **Custom repositories**.
3. Add `https://github.com/bditter/maytag-appliance-homeassistant` as an
   **Integration** repository.
4. Install **Maytag Appliance** and restart Home Assistant.

### Manual

1. Copy `custom_components/maytag_appliance` into the Home Assistant
   `custom_components` directory.
2. Restart Home Assistant.

## Configuration

1. Remove the old `maytag_dryer` sensor platform block from
   `configuration.yaml` if upgrading from the YAML integration.
2. Open **Settings > Devices & services > Add integration**.
3. Search for **Maytag Appliance** and enter the Maytag app account. Supported
   washers and dryers are discovered automatically.

To update the password later, open the integration and choose **Configure**,
then **Reconfigure**.

## Upgrading From 1.1.x

Version 1.2.0 automatically removes the previously saved appliance-ID lists
and discovers washers and dryers from the Maytag account. Existing entities
keep their SAID-based unique IDs, so removing the integration is normally not
required.

After updating, restart Home Assistant. If the integration still shows the old
appliance-ID fields or does not discover the appliances, remove the integration
entry and add **Maytag Appliance** again using only the email and password.

## Attribution

This project is based on
[jdeath/maytag_dryer_homeassistant](https://github.com/jdeath/maytag_dryer_homeassistant).
It retains the original washer/dryer behavior and compatibility attributes
while adding GUI configuration and config-entry lifecycle support.

## License

Licensed under the [MIT License](LICENSE.txt). The original copyright and
license notice from `jdeath/maytag_dryer_homeassistant` are retained.
