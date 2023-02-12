from .api import (APIItems, APIItem)

END_POINT = "/insight/clients"


class KnownClients(APIItems):
    def __init__(self, request):
        super().__init__(request, END_POINT, "mac", KnownClient, data_key="data")

    async def async_set_block(self, mac: str, block: bool) -> None:
        await self._request("POST", "/cmd/clients/{}/{}".format(mac, block and "block" or "unblock"))

class KnownClient(APIItem):
    @property
    def mac(self) -> str:
        return self._raw.get("mac", "")

    @property
    def name(self) -> str | None:
        return self._raw.get("name", None)

    @property
    def wireless(self) -> bool:
        return self._raw.get("wireless", False)

    @property
    def guest(self) -> bool:
        return self._raw.get("guest", False)

    @property
    def download(self) -> int:
        return self._raw.get("download", 0)

    @property
    def upload(self) -> int:
        return self._raw.get("upload", 0)

    @property
    def duration(self) -> int:
        return self._raw.get("duration", 0)

    @property
    def last_seen(self) -> int:
        return self._raw.get("lastSeen", 0)

    @property
    def block(self) -> bool:
        return self._raw.get("block", False)

    @property
    def manager(self) -> bool:
        return self._raw.get("manager", False)

    def __repr__(self):
        name = self.name or self.mac
        return f"<Client {name}: {self.mac} {self._raw}>"
