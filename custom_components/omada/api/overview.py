from .api import (APIItem)

END_POINT = "/overviewDiagram"

class OverviewDiagram(APIItem):

    # WAN
    @property
    def wan_capacity(self):
        return self._raw.get("netCapacity", "")
    def wan_utilisation(self):
        return self._raw.get("netUtilization", "")

    @property
    def power_consumption(self):
        return self._raw.get("powerConsumption", "")

    # Gateway
    @property
    def gateway_total(self):
        return self._raw.get("totalGatewayNum", "")
    @property
    def gateway_connected(self):
        return self._raw.get("connectedGatewayNum", "")
    @property
    def gateway_disconnected(self):
        return self._raw.get("disconnectedGatewayNum", "")

    # Switch
    @property
    def switch_total(self):
        return self._raw.get("totalSwitchNum", "")
    @property
    def switch_connected(self):
        return self._raw.get("connectedSwitchNum", "")
    @property
    def switch_disconnected(self):
        return self._raw.get("disconnectedSwitchNum", "")

    # Ports
    @property
    def ports_total(self):
        return self._raw.get("totalPorts", "")
    @property
    def ports_available(self):
        return self._raw.get("availablePorts", "")

    # AP
    @property
    def ap_total(self):
        return self._raw.get("totalApNum", "")
    @property
    def ap_connected(self):
        return self._raw.get("connectedApNum", "")
    @property
    def ap_disconnected(self):
        return self._raw.get("disconnectedApNum", "")
    @property
    def ap_isolated(self):
        return self._raw.get("isolatedApNum", "")

    # Clients
    @property
    def client_total(self):
        return self._raw.get("totalClientNum", "")
    @property
    def client_wired(self):
        return self._raw.get("wiredClientNum", "")
    @property
    def client_wireless(self):
        return self._raw.get("wirelessClientNum", "")
    @property
    def client_guest(self):
        return self._raw.get("guestNum", "")

    def __repr__(self):
        return f"<Overview {self._raw}>"