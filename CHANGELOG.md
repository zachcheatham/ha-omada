# Changelog

## 0.9.0
- Added reconnect all clients button
- Added POE Statistics (Thanks @bmadzinski)
- Added option to reconfigure integration (user, password, controller url)
- Fixed errors when reloading the integration
- Fixed issue when catching unknown site errors during setup.

## 0.8.0
- Added device reboot button (Thanks @RvRijsselt)
- Fixed OptionsFlow incompatibility with Home Assistant 2025.12

## 0.7.0
- Added wired client support (Thanks @jonathanhoskin)
- Added latest WiFi standards (Thanks @jonathanhoskin)

## 0.6.1
- Fixes issue related to timeouts in newer versions of HA
- Fixes issue related to missing IP addresses from the Omada Controlller
- Fixes regression causing entities to remain after the device was removed from the Omada Controller

## 0.5.0
- Add support for Omada Controller 5.13+
- Add sensor and trigger for WLAN optimization
- Fix device upgrades

## 0.4.3
- Fixes bug causing the configuration flow to break.

## 0.4.2
- Fix errors related to tx and rx rates on unsupported devices
- Fix an error when re-configuring the SSID filter after an SSID was removed from Omada.

## 0.4.1
- Fix issue related to pulling radio state and wifi mode of wired devices.
- Increase the API request timeout to 30 seconds.

## 0.4.0
- Added client bandwidth, activity, and uptime sensors.
- Added client WiFi blocking switches.
- Added HA devices to associate client entities together.
- Added device bandwidth, uptime, clients, CPU, and memory sensors.
- Added AP band utilization sensors.
- Added AP radio switches
- Added new integration configuration options for controlling which entity types are loaded.
- Added new integration configuration to add an additional timeout to device trackers before they are marked Away.
- Entities will now move to unavailable state when the controller becomes unreachable.
- Client device tracker attributes now include the mac address, host name, and connected AP name.
- Client device tracker AP mac addresses are now formatted as 00:00:00:00:00:00
- Removed site name prefix from access point devices.
- Remove use of deprecated HA functions.


## 0.3.0
- Added additional AP and client information and statistics (@ping-localhost)

## 0.2.1
- Fixed a permissions error by using a different endpoint for determing the site id (@sogood007)
- Allow Home Assistant to properly retry the integration's setup if Omada is unavailable when Home Assistant starts.

## 0.2.0

- Add support for the API changes introduced in version 5.0.0 of the Omada Controller. This has not been fully tested as I do not have a production v5 controller to test on. It is fully working on my device-less test install of 5.0.15

## 0.1.2

- Restore compatibility with devices running 4.4.6 as hardware controllers are still stuck on this version.

## 0.1.1
- Re-attempt logins after connectivity failures. This should fix lost connections after controller restarts.
- Add support for controller 4.4.8
- Remove support for controllers < 4.4.8 (Pre-Log4J Patches)
- Enhance error messaging during setup

## 0.1.0
- Add device state and tracking (PR #1)

## 0.0.3
- Fix errors when client disappears from known client list.

## 0.0.2
- Fix restoring filtered devices.
- Listen for HA configuration changes

## 0.0.1
- Initial Release