# TP-Link Omada Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Integrate your TP-Link Omada SDN Controller with Home Assistant. This custom component allows you to monitor network clients and Omada devices, control aspects of your network, and leverage Omada data within your automations.

This integration is designed to be installed via [HACS](https://hacs.xyz/).

## Features

### Client Monitoring & Management

* **Device Tracker:** Presence detection for both wired and wireless clients.
  * Attributes include: IP, MAC, hostname, connection type (wired/wireless), connected AP, SSID, signal strength, etc.
  * Configurable disconnect timeout for marking clients as away.
* **Sensors:**
  * Total Downloaded & Uploaded data.
  * Current RX/TX Activity.
  * RSSI & SNR for wireless clients.
  * Uptime.
  * Power Save status.
* **Controls:**
  * Block/Unblock clients.
  * Reconnect wireless clients.
* **Filtering:** Track clients only on specific SSIDs.

### Omada Device (APs, Gateways, Switches) Monitoring & Management

* **Device Tracker:** Presence detection for Omada network devices.
* **Sensors:**
  * Total Downloaded & Uploaded data.
  * Current RX/TX Activity.
  * CPU & Memory Usage.
  * Uptime.
  * Connected client counts (total, 2.4GHz, 5GHz, 6GHz, guests, users).
  * AP Radio Utilization: TX/RX utilization and interference levels for 2.4GHz, 5GHz, and 6GHz bands.
* **Controls (Primarily for Access Points):**
  * Enable/Disable 2.4GHz, 5GHz, and 6GHz radios (switches).
  * Enable/Disable individual SSIDs per AP (switches).
* **Firmware Updates:**
  * Update entity to show available firmware, current version, and trigger upgrades.
  * Release notes for pending updates.

### Controller Features

* **Sensors:**
  * Total number of connected clients across the site.
  * WLAN Optimization (AI RF Planning) running status.
* **Controls:**
  * Start WLAN Optimization (AI RF Planning).

### Configurability

* Granular control over which types of entities are created (e.g., disable bandwidth sensors if not needed).
* Adjustable scan intervals for main data and detailed data.

### Comparison with Official Home Assistant Support

Home Assistant now includes an official core integration for TP-Link Omada SDN. Here's a comparison to help you choose based on information from the official Home Assistant Wiki as of May 2025:

| Feature | Official Integration | Custom |
| :-------------------------------- | :------------------------------------------------------------- | :------------------------------------------------------------- |
| **Installation** | Built-in, configured via Devices & Services. | Requires HACS, then configured via Devices & Services. |
| **Controller Version Support** | 5.1.0 and later. | 4.4.8+ and v5.x.x |
| **Device Support (General)** | Basic status, CPU/Memory, Firmware updates for all devices. | Similar, plus device trackers for Omada hardware. |
| **Network Switch Control** | PoE per-port enable/disable. | Currently no specific per-port PoE exposed (focuses on APs/Clients). |
| **Internet Gateway Control** | WAN/LAN connectivity, Online detection, Connect/Disconnect WAN. | Limited gateway-specific controls (focuses on APs/Clients). |
| **Access Point Control** | Not explicitly detailed in official docs beyond basic status. | Radio (2G/5G/6G) on/off, SSID on/off per AP. |
| **Client Device Tracking** | Tracks Wi-Fi clients (disabled by default). | Tracks wired and wireless clients. |
| **Client Information** | Basic tracking for presence. | IP, MAC, hostname, AP, SSID, signal, etc. |
| **Client Sensors** | Not detailed. | Download/Upload, RX/TX rate, RSSI, SNR, Uptime, Power Save. |
| **Client Controls** | Not detailed. | Block/Unblock switch, Reconnect button. |
| **Client Filtering** | All known Wi-Fi clients. | SSID-based filtering for wireless clients. |
| **AP Radio/Bandwidth Sensors** | Not detailed. | Client counts per band, radio utilization (TX/RX/Interference). |
| **WLAN Optimization Control** | Not detailed. | Binary sensor for status, button to start. |
| **Configuration Granularity** | Primarily site selection. | Toggle individual sensor/switch types for clients and devices, adjust scan intervals, disconnect timeouts. |
| **Data Update Frequency** | Default HA polling, client refresh via service call. | Configurable scan intervals for basic and detailed data. |
| **Cloud Controller Support** | No. | No. |

You can potentially run both integrations if they target different aspects or if you are migrating, but be mindful of potential API rate limiting on your Omada Controller.

If it ever becomes the case that the official integration satifies my own personal needs, I will be switching to it and archiving this repo. Until then, this will continue to be maintained and new features added as time allows.

## Prerequisites

* A running Home Assistant instance.
* [HACS (Home Assistant Community Store)](https://hacs.xyz/) installed.
* A TP-Link Omada SDN Controller (Software* or Hardware Controller). Ensure it's accessible from your Home Assistant instance network-wise.

## Installation

1. Ensure HACS is installed.
2. Open HACS in Home Assistant (usually in the sidebar).
3. Go to **Integrations**.
4. Click the 3-dots menu in the top right and select **Custom Repositories**.
    * URL: `https://github.com/zachcheatham/ha-omada`
    * Category: `Integration`
    * Click **ADD**.
5. Search for "TP-Link Omada" in HACS and click **INSTALL**.
6. Restart Home Assistant.

## Configuration

1. Go to **Settings > Devices & Services** in Home Assistant.
2. Click the **+ ADD INTEGRATION** button (bottom right).
3. Search for "TP-Link Omada" and select it.
4. You will be prompted for the following information:
    * **URL:** The full URL to access your Omada Controller (e.g., `https://omada.yourdomain.com` or `http://192.168.1.10`).
    * **Site:** The name of the Omada site you want to integrate (default is "Default").
    * **Username:** Your Omada Controller username.
    * **Password:** Your Omada Controller password.
    * **Verify SSL:** Check this if your controller uses a valid SSL certificate. Uncheck for self-signed certificates or HTTP.
5. Click **SUBMIT**.

    *Tip: If the integration is encountering an API or related error during configuration, ensure your site name is correct!*

### Options

After successful setup, you can further customize the integration's behavior:

1. Go to **Settings > Devices & Services**.
2. Find your TP-Link Omada integration entry and click **CONFIGURE**.
3. You can adjust:
    * **Scan Intervals:** How frequently to poll the controller for basic and detailed updates.
    * **Tracking:** Enable/disable tracking for clients or Omada devices.
    * **Client Entity Options:** Toggle specific sensors (bandwidth, uptime) and controls (block switch) for clients. Set disconnect timeout and SSID filters.
    * **Device Entity Options:** Toggle specific sensors (bandwidth, statistics, client counts, radio utilization) and controls for Omada devices.

## Supported Controller Versions

This integration is tested and developed against various Omada Controller versions. Generally, it supports:

* Omada Controller v5.x (including the latest 5.13.x versions).

Please note that TP-Link may introduce API changes in new controller versions. If you encounter issues, check the [CHANGELOG.md](CHANGELOG.md) or open an issue.
Additionally, this integration is known to not be compatible with the cloud version of Omada SDN.

## Future Features

* More comprehensive support for Omada switches and gateways.
* Individual client-based filtering for entity creation (beyond SSID).
* Additional SDN and site-wide controls and statistics.
* PoE Controls

## Troubleshooting

* **Connectivity Issues:** Ensure your Home Assistant instance can reach the Omada Controller's IP address and port. Ensure "Verify SSL" is set appropriately.
* **API Errors:** Double-check your URL, username, password, and site name.
* **Entities Not Appearing:** Verify the options in the integration's configuration to ensure the desired entity types are enabled. Check Home Assistant logs for errors.
* For other issues, please check the Home Assistant logs and [open an issue](https://github.com/zachcheatham/ha-omada/issues) on GitHub with relevant log details.

## Contributing

Contributions are welcome! Please feel free to fork the repository, make your changes, and submit a pull request.
