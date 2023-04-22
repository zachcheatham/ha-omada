import logging

from typing import Any, Dict

from .api import (APIItems, APIItem)

END_POINT = "/devices"
AP_DETAILS_END_POINT = "/eaps/%key"
FIRMWARE_END_POINT = "/devices/%key/firmware"

AP_DETAILS_PROPERTIES = ["ssidOverrides", "wlanId"]
FIRMWARE_PROPERTIES = ["lastFwVer", "fwReleaseLog"]

LOGGER = logging.getLogger(__name__)


class Device(APIItem):
    """Defines all the properties for a Device"""

    @property
    def type(self) -> str:
        return self._raw.get("type", "")

    @property
    def mac(self) -> str:
        return self._raw.get("mac", "")

    @property
    def name(self) -> str:
        return self._raw.get("name", "")

    @property
    def model(self) -> str:
        return self._raw.get("compoundModel", "")

    @property
    def supports_6ghz(self) -> bool:
        return self._raw.get("deviceMisc", {}).get("support6g", False)

    @property
    def supports_5ghz(self) -> bool:
        return self._raw.get("deviceMisc", {}).get("support5g", False)

    @property
    def firmware(self) -> str:
        return self._raw.get("firmwareVersion", "")

    @property
    def firmware_upgrade(self) -> bool:
        return self._raw.get("needUpgrade", False)

    @property
    def firmware_latest(self) -> str:
        return self._details.get("lastFwVer", "")

    @property
    def firmware_latest_rn(self) -> str:
        return self._details.get("fwReleaseLog", "")

    @property
    def status(self) -> int:
        return int(self._raw.get("status", 0))

    @property
    def status_category(self) -> int:
        return int(self._raw.get("statusCategory", 14))

    @property
    def uptime(self) -> int:
        return int(self._raw.get("uptimeLong", 0))

    @property
    def cpu(self) -> int:
        return int(self._raw.get("cpuUtil", 0))

    @property
    def memory(self) -> int:
        return int(self._raw.get("memUtil", 0))

    @property
    def wlan_id(self) -> str:
        return self._details.get("wlanId", None)

    # Connectivity

    @property
    def mesh(self) -> bool:
        return self._raw.get("wirelessLinked", False)

    @property
    def uplink(self):
        return self._raw.get("uplink", "")

    @property
    def ip(self) -> str:
        return self._raw.get("ip", "")

    @property
    def ssid_overrides(self) -> list[Dict[str, Any]]:
        return self._details.get("ssidOverrides", [])

    @property
    def clients(self) -> int:
        return int(self._raw.get("clientNum", 0))

    @property
    def clients_2ghz(self) -> int:
        return int(self._raw.get("clientNum2g", 0))

    @property
    def clients_5ghz(self) -> int:
        return int(self._raw.get("clientNum5g", 0))

    @property
    def clients_6ghz(self) -> int:
        return int(self._raw.get("clientNum6g", 0))

    @property
    def guests(self) -> int:
        return int(self._raw.get("guestNum", 0))

    @property
    def users(self) -> int:
        return int(self._raw.get("userNum", 0))

    # Radio Stats

    @property
    def radio_enabled_2ghz(self) -> bool | None:
        return self._raw.get("radioSetting2g", {}).get("radioEnable", None)

    @property
    def radio_enabled_5ghz(self) -> bool | None:
        return self._raw.get("radioSetting5g", {}).get("radioEnable", None)

    @property
    def radio_enabled_6ghz(self) -> bool | None:
        return self._raw.get("radioSetting6g", {}).get("radioEnable", None)

    @property
    def radio_mode_2ghz(self) -> str | None:
        return self._raw.get("wp2g", {}).get("rdMode", None)

    @property
    def radio_mode_5ghz(self) -> str | None:
        return self._raw.get("wp5g", {}).get("rdMode", None)

    @property
    def radio_mode_6ghz(self) -> str | None:
        return self._raw.get("wp6g", {}).get("rdMode", None)

    @property
    def bandwidth_2ghz(self) -> str | None:
        return self._raw.get("wp2g", {}).get("bandWidth", None)

    @property
    def bandwidth_5ghz(self) -> str | None:
        return self._raw.get("wp5g", {}).get("bandWidth", None)

    @property
    def bandwidth_6ghz(self) -> str | None:
        return self._raw.get("wp6g", {}).get("bandWidth", None)

    @property
    def tx_power_2ghz(self) -> int | None:
        return self._raw.get("wp2g", {}).get("txPower", None)

    @property
    def tx_power_5ghz(self) -> int | None:
        return self._raw.get("wp5g", {}).get("txPower", None)

    @property
    def tx_power_6ghz(self) -> int | None:
        return self._raw.get("wp6g", {}).get("txPower", None)

    @property
    def tx_utilization_2ghz(self) -> int | None:
        return self._raw.get("wp2g", {}).get("txUtil", None)

    @property
    def tx_utilization_5ghz(self) -> int | None:
        return self._raw.get("wp5g", {}).get("txUtil", None)

    @property
    def tx_utilization_6ghz(self) -> int | None:
        return self._raw.get("wp6g", {}).get("txUtil", None)

    @property
    def rx_utilization_2ghz(self) -> int | None:
        return self._raw.get("wp2g", {}).get("rxUtil", None)

    @property
    def rx_utilization_5ghz(self) -> int | None:
        return self._raw.get("wp5g", {}).get("rxUtil", None)

    @property
    def rx_utilization_6ghz(self) -> int | None:
        return self._raw.get("wp6g", {}).get("rxUtil", None)

    @property
    def interference_utilization_2ghz(self) -> int | None:
        return self._raw.get("wp2g", {}).get("interUtil", None)

    @property
    def interference_utilization_5ghz(self) -> int | None:
        return self._raw.get("wp5g", {}).get("interUtil", None)

    @property
    def interference_utilization_6ghz(self) -> int | None:
        return self._raw.get("wp6g", {}).get("interUtil", None)

    # Throughput

    @property
    def upload(self) -> int:
        return int(self._raw.get("upload", 0))

    @property
    def download(self) -> int:
        return int(self._raw.get("download", 0))

    @property
    def tx_rate(self) -> int:
        return int(self._raw.get("txRate", 0))

    @property
    def rx_rate(self) -> int:
        return int(self._raw.get("rxRate", 0))

    def __repr__(self):
        name = self.name or self.mac
        type = self.type or '!'
        return f"<Device:{type} {name}:{self.mac} {self._raw}>"


class Devices(APIItems):

    _has_details = True

    def __init__(self, request):
        super().__init__(request, END_POINT, "mac", Device)

    async def async_set_radio_enable(self, mac: str, radio: int, enable: bool) -> None:

        key = ""

        if radio == 2:
            key = "radioSetting2g"
        elif radio == 5:
            key = "radioSetting5g"
        elif radio == 6:
            key = "radioSetting6g"

        data = {
            key: {
                "radioEnable": enable
            }
        }

        await self._request("PATCH", f"/eaps/{mac}", json=data)

    async def async_set_ssid_enable(self, mac: str, existing_overrides: list[Dict[str, Any]], wlan_id: str, ssid: str, enabled: bool) -> None:

        for ssid_override in existing_overrides:
            if ssid_override["globalSsid"] == ssid:
                ssid_override["ssidEnable"] = enabled
                break

        await self._request("PATCH", f"/eaps/{mac}", json={"wlanId": wlan_id, "ssidOverrides": existing_overrides})

    async def trigger_update(self, mac: str) -> None:
        await self._request("GET", f"/cmd/devices/{mac}/onlineUpgrade")

    async def update_details(self, key: str, item: Device) -> None:

        if item.type == "ap":
            ap_details = await self._request("GET", AP_DETAILS_END_POINT.replace("%key", key))
            for prop in AP_DETAILS_PROPERTIES:
                if prop in ap_details:
                    item._details[prop] = ap_details[prop]

        if item.firmware_upgrade:
            firmware_details = await self._request("GET", FIRMWARE_END_POINT.replace("%key", key))
            for prop in FIRMWARE_PROPERTIES:
                if prop in firmware_details:
                    item._details[prop] = firmware_details[prop]
