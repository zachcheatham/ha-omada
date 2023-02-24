# Home Assistant TP-Link Omada Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Adds Omada SDN Controller support to Home assistant. This integration requires [HACS](https://hacs.xyz).

## Features

- Device tracker for clients.
- Client and device bandwidth sensors.
- Client and device statistics sensors.
- WLAN Radio controls
- WLAN SSID controls
- Client blocking toggles.
- SSID filter.

## Planned Features

- Better wired client support (help wanted.)
- Better switch and router support (help wanted.)
- Individual client filters.
- SDN and site controls and statistics.



## Installation

Recommended to be installed via [HACS](https://github.com/hacs/integration)

1. Go to HACS -> Integrations
2. [Add this repo to your HACS custom repositories](https://hacs.xyz/docs/faq/custom_repositories)
3. Search for TP-Link Omada and install.
4. Restart Home Assistant
5. Open Home Assistant Settings -> Devices & Serivces
6. Shift+reload your browser to clear config flow caches.
7. Click ADD INTEGRATION
8. Search for TP-Link Omada
9. Enter the URL you use to access your Omada SDN, the username you would like HA to connect with, and its password.
10. If no errors occur, you're all set! Otherwise, feel free to browse the issue track or open a new issue to help resolve the issue.
