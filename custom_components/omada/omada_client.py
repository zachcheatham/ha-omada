from typing import Any

from homeassistant.core import callback
from homeassistant.helpers import device_registry, entity_registry
from homeassistant.helpers.entity_registry import async_entries_for_device
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .omada_entity import OmadaEntity


class OmadaClient(OmadaEntity):

    @callback
    async def async_update(self):
        if (self._controller.option_ssid_filter
                and self.key in self._controller.api.clients
                and self._controller.api.clients[self.key].ssid not in self._controller.option_ssid_filter):

            await self.remove()
        else:
            self.async_write_ha_state()

    @callback
    async def options_updated(self):
        if (self._controller.option_ssid_filter
            and self.key in self._controller.api.clients
                and self._controller.api.clients[self.key].ssid not in self._controller.option_ssid_filter):
            await self.remove()
