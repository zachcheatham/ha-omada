from .api import (APIItems, APIItem)

END_POINT = "/insight/clients"

class KnownClients(APIItems):

    def __init__(self, request):
        super().__init__(request, END_POINT, "mac", KnownClient, data_key="data")

class KnownClient(APIItem):

    @property
    def mac(self):
        return self._raw.get("mac", "")

    @property
    def name(self):
        return self._raw.get("name", "")

    @property
    def wireless(self):
        return self._raw.get("wireless")

    @property
    def guest(self):
        return self._raw.get("guest")

    @property
    def download(self):
        return self._raw.get("download")

    @property
    def upload(self):
        return self._raw.get("upload")

    @property
    def duration(self):
        return self._raw.get("duration")

    @property
    def last_seen(self):
        return self._raw.get("lastSeen")

    @property
    def block(self):
        return self._raw.get("block")

    @property
    def manager(self):
        return self._raw.get("manager")

    def __repr__(self):
        name = self.name or self.mac
        return f"<Client {name}: {self.mac} {self._raw}>"