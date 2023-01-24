from typing import Any

from homeassistant.core import callback
from homeassistant.helpers import device_registry, entity_registry
from homeassistant.helpers.entity_registry import async_entries_for_device
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .controller import OmadaController

class OmadaEntity(Entity):

    DOMAIN = ""
    TYPE = ""
    
    def __init__(self, controller: OmadaController, mac: str) -> None:

        self._mac = mac
        self._controller = controller
        self._controller.entities[self.DOMAIN][self.TYPE].add(self.key)

    async def async_added_to_hass(self) -> None:
        for signal, method in (
            (self._controller.signal_options_update, self.options_updated),
            (self._controller.signal_update, self.async_update)
        ):
            self.async_on_remove(
                async_dispatcher_connect(self.hass, signal, method))

    @property
    def unique_id(self) -> str | None:
        return f"{self.TYPE}-{self._mac}"
    
    @property
    def key(self) -> Any:
        return self._mac

    @property
    def name(self) -> str:
        return self.base_name
        
    @property
    def base_name(self) -> str:
        if self._mac in self._controller.api.known_clients:
            return self._controller.api.known_clients[self.key].name
        elif self._mac in self._controller.api.devices:
            return self._controller.api.devices[self.key].name
        else:
            return self._mac
        
    @property
    def available(self) -> bool:
        return self._controller.available
    
    @property
    def should_poll(self) -> bool:
        return False    
    
    @property
    def device_info(self) -> DeviceInfo | None:
        return DeviceInfo(
            connections={(CONNECTION_NETWORK_MAC, self.key)},
            default_name=self.base_name
        )
    
    @callback
    async def async_update(self):
        self.async_write_ha_state()
    
    async def remove(self):
        er = entity_registry.async_get(self.hass)

        entity_entry = er.async_get(self.entity_id)
        if not entity_entry:
            await self.async_remove(force_remove=True)
            return

        dr = device_registry.async_get(self.hass)
        device_entry = dr.async_get(entity_entry.device_id)
        if not device_entry:
            er.async_remove(self.entity_id)
            return

        if (
            len(
                entries_for_device := async_entries_for_device(
                    er,
                    entity_entry.device_id,
                    include_disabled_entities=True,
                )
            )
        ) == 1:
            dr.async_remove_device(device_entry.id)
            return

        if (
            len(
                entries_for_device_from_this_config_entry := [
                    entry_for_device
                    for entry_for_device in entries_for_device
                    if entry_for_device.config_entry_id
                    == self._controller._config_entry.entry_id
                ]
            )
            != len(entries_for_device)
            and len(entries_for_device_from_this_config_entry) == 1
        ):
            dr.async_update_device(
                entity_entry.device_id,
                remove_config_entry_id=self._controller._config_entry.entry_id,
            )

        er.async_remove(self.entity_id)

    @callback
    async def options_updated(self):
        pass