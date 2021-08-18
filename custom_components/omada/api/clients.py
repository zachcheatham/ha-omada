from .api import (APIItems, APIItem)

END_POINT = "/clients"

class Clients(APIItems):

    def __init__(self, request):
        super().__init__(request, END_POINT, "mac", Client, data_key="data")

class Client(APIItem):

    @property
    def mac(self):
        return self._raw.get("mac", "")

    @property
    def name(self):
        return self._raw.get("name", "")

    @property
    def device_type(self):
        return self._raw.get("deviceType", "")

    @property
    def ip(self):
        return self._raw.get("ip", "")

    @property
    def connect_type(self):
        return self._raw.get("connectType", "")

    @property
    def connect_dev_type(self):
        return self._raw.get("connectDevType", "")

    @property
    def wireless(self):
        return self._raw.get("wireless")

    @property
    def ssid(self):
        return self._raw.get("ssid", "")

    @property
    def signal_level(self):
        return self._raw.get("signalLevel")

    @property
    def signal_rank(self):
        return self._raw.get("signalRank")

    @property
    def wifi_mode(self):
        return self._raw.get("wifiMode")

    @property
    def ap_name(self):
        return self._raw.get("apName")

    @property
    def ap_mac(self):
        return self._raw.get("apMac")

    @property
    def radio_id(self):
        return self._raw.get("raduiId")

    @property
    def channel(self):
        return self._raw.get("channel")

    @property
    def rx_rate(self):
        return self._raw.get("rxRate")

    @property
    def tx_rate(self):
        return self._raw.get("txRate")

    @property
    def power_save(self):
        return self._raw.get("powerSave")

    @property
    def rssi(self):
        return self._raw.get("rssi")

    @property
    def activity(self):
        return self._raw.get("activity")

    @property
    def traffic_down(self):
        return self._raw.get("trafficDown")

    @property
    def traffic_up(self):
        return self._raw.get("trafficUp")

    @property
    def uptime(self):
        return self._raw.get("uptime")

    @property
    def last_seen(self):
        return self._raw.get("lastSeen")

    @property
    def auth_status(self):
        return self._raw.get("auth_status")

    @property
    def guest(self):
        return self._raw.get("guest")

    @property
    def active(self):
        return self._raw.get("active")

    @property
    def manager(self):
        return self._raw.get("manager")

    @property
    def down_packet(self):
        return self._raw.get("downPacket")

    @property
    def up_packet(self):
        return self._raw.get("upPacket")

    def __repr__(self):
        name = self.name or self.mac
        return f"<Client {name}: {self.mac} {self._raw}>"