# Changelog

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