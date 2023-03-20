from .api import (APIItems, APIItem)

END_POINT = "/clients"

WIFI_MODE = [
    "11a",
    "11b",
    "11g",
    "11na",
    "11ng",
    "11ac",
    "11axa",
    "11axg"
]

RADIO = [
    "2.4gz",
    "5ghz",
    "5ghz",
    "6ghz"
]


class Clients(APIItems): 
    def __init__(self, request):
        super().__init__(request, END_POINT, "mac", Client, data_key="data")


class Client(APIItem):
    """Defines all the properties for a Client"""

    @property
    def mac(self) -> str:
        return self._raw.get("mac", "")

    @property
    def name(self) -> str | None:
        return self._raw.get("name")

    @property
    def hostname(self) -> str | None:
        return self._raw.get("hostName")

    @property
    def device_type(self) -> str | None:
        return self._raw.get("deviceType")

    @property
    def ip(self) -> str | None:
        return self._raw.get("ip")

    @property
    def connect_type(self) -> int | None:
        return self._raw.get("connectType")

    @property
    def connect_dev_type(self) -> str | None:
        return self._raw.get("connectDevType")

    @property
    def wireless(self) -> bool:
        return self._raw.get("wireless", False)

    @property
    def ssid(self) -> str | None:
        return self._raw.get("ssid")

    @property
    def signal_level(self) -> int:
        return self._raw.get("signalLevel", 0)

    @property
    def signal_rank(self) -> int:
        return self._raw.get("signalRank", 0)

    @property
    def wifi_mode(self) -> str:
        return WIFI_MODE[self._raw.get("wifiMode", 0)]

    @property
    def ap_name(self) -> str | None:
        return self._raw.get("apName")

    @property
    def ap_mac(self) -> str | None:
        return self._raw.get("apMac")

    @property
    def radio(self) -> str:
        return RADIO[self._raw.get("radioId", 0)]

    @property
    def channel(self) -> int | None:
        return self._raw.get("channel")

    @property
    def rx_rate(self) -> int | None:
        return self._raw.get("rxRate")

    @property
    def tx_rate(self) -> int | None:
        return self._raw.get("txRate")

    @property
    def power_save(self) -> bool:
        return self._raw.get("powerSave", False)

    @property
    def rssi(self) -> int | None:
        return self._raw.get("rssi")

    @property
    def activity(self) -> int:
        return self._raw.get("activity", 0)

    @property
    def traffic_down(self) -> int:
        return self._raw.get("trafficDown", 0)

    @property
    def traffic_up(self) -> int:
        return self._raw.get("trafficUp", 0)

    @property
    def uptime(self) -> int:
        return self._raw.get("uptime", -1)

    @property
    def last_seen(self) -> int:
        return self._raw.get("lastSeen", -1)

    @property
    def auth_status(self) -> int | None:
        return self._raw.get("authStatus")

    @property
    def guest(self) -> bool:
        return self._raw.get("guest", False)

    @property
    def active(self) -> bool:
        return self._raw.get("active", False)

    @property
    def manager(self) -> bool:
        return self._raw.get("manager", False)

    @property
    def down_packet(self) -> int:
        return self._raw.get("downPacket", 0)

    @property
    def up_packet(self) -> int:
        return self._raw.get("upPacket", 0)

    def __repr__(self):
        name = self.name or self.mac
        return f"<Client {name}: {self.mac} {self._raw}>"
