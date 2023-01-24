from .api import (APIItems, APIItem)

END_POINT = "/devices"


class Devices(APIItems):
    def __init__(self, request):
        super().__init__(request, END_POINT, "mac", Device)


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
