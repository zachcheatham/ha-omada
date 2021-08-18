from .api import (APIItems, APIItem)

END_POINT = "/topology"

class Devices(APIItems):

    def __init__(self, request):
        super().__init__(request, END_POINT, "mac", Device)

class Device(APIItem):

    @property
    def mac(self):
        return self._raw.get("mac", "")

    @property
    def name(self):
        return self._raw.get("name", "")

    @property
    def type(self):
        return self._raw.get("type", "")

    @property
    def model(self):
        return self._raw.get("model", "")

    @property
    def model_version(self):
        return self._raw.get("modelVersion", "")

    @property
    def client_count(self):
        return self._raw.get("clientCount", "")

    @property
    def successors(self):
        return self._raw.get("successors", "")

    # AP specific
    @property
    def channel_2g(self):
        return self._raw.get("channel2g", "")

    @property
    def channel_5g(self):
        return self._raw.get("channel5g", "")

    @property
    def rd_mode_2g(self):
        return self._raw.get("rdMode2g", "")

    @property
    def rd_mode_5g(self):
        return self._raw.get("rdMode5g", "")

    @property
    def wired_uplink(self):
        # wireUpLink
        #   duplex
        #   linkSpeed
        return self._raw.get("wireUpLink", "")

    @property
    def wireless_uplink(self):
        # wirelessUpLink
        #   rssi
        #   rssiPercent
        #   rxRate
        #   txRate
        return self._raw.get("wirelessUpLink", "")

    def __repr__(self):
        name = self.name or self.mac
        type = self.type or '!'
        return f"<Device {type}|{name}: {self.mac} {self._raw}>"