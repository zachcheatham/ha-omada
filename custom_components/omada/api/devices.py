from .api import (APIItems, APIItem)

END_POINT = "/devices"

class Devices(APIItems):

    def __init__(self, request):
        super().__init__(request, END_POINT, "mac", Device)

class Device(APIItem):

    @property
    def type(self):
        return self._raw.get("type", "")

    @property
    def mac(self):
        return self._raw.get("mac", "")

    @property
    def name(self):
        return self._raw.get("name", "")

    @property
    def model(self):
        return self._raw.get("compoundModel", "")

    @property
    def firmware(self):
        return self._raw.get("firmwareVersion", "")

    @property
    def firmware_upgrade(self):
        return self._raw.get("needUpgrade", "")

    @property
    def ip(self):
        return self._raw.get("ip", "")

    @property
    def upload(self):
        return self._raw.get("upload", "")

    @property
    def download(self):
        return self._raw.get("download", "")


    @property
    def tx_rate(self):
        return self._raw.get("txRate", "")

    @property
    def rx_rate(self):
        return self._raw.get("rxRate", "")

    @property
    def mesh(self):
        return self._raw.get("wirelessLinked", "")


    def __repr__(self):
        name = self.name or self.mac
        type = self.type or '!'
        return f"<Device {type}|{name}: {self.mac} {self._raw}>"