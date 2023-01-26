from __future__ import annotations

import logging

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.core import callback
from homeassistant.helpers import device_registry, entity_registry
from homeassistant.helpers.entity_registry import async_entries_for_device
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import Entity, EntityDescription, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import ATTR_MANUFACTURER as ATTR_OMADA_MANUFACTURER
from .api.controller import Controller
from .api.clients import Client
from .api.devices import Device

if TYPE_CHECKING:
    from .controller import OmadaController


LOGGER = logging.getLogger(__name__)

@callback
def entity_available_fn(controller: OmadaController, mac: str) -> bool:
    return controller.available


@callback
def device_device_info_fn(api: Controller, mac: str) -> DeviceInfo:
    device: Device = api.devices[mac]

    return DeviceInfo(
        connections={(CONNECTION_NETWORK_MAC, mac)},
        manufacturer=ATTR_OMADA_MANUFACTURER,
        model=device.model,
        sw_version=device.firmware,
        name=device.name,
    )


@callback
def client_device_info_fn(api: Controller, mac: str) -> DeviceInfo:
    client: Client = api.known_clients[mac]

    return DeviceInfo(
        connections={(CONNECTION_NETWORK_MAC, mac)},
        default_name=client.name
    )


@callback
def unique_id_fn(mac: str, entity_type: str) -> str:
    return f"{entity_type}-{mac}"


@dataclass
class OmadaDescriptionMixin():
    domain: str
    allowed_fn: Callable[[OmadaController, str], bool]
    supported_fn: Callable[[OmadaController, str], bool]
    available_fn: Callable[[OmadaController, str], bool]
    device_info_fn: Callable[[Controller, str], bool]
    name_fn: Callable[[Controller, str, str], str]
    unique_id_fn: Callable[[OmadaController, str], str]


@dataclass
class OmadaEntityDescription(EntityDescription, OmadaDescriptionMixin):
    """Omada enitty description"""


class OmadaEntity(Entity):

    entity_description: OmadaEntityDescription

    _attr_should_poll = False
    _attr_unique_id: str

    def __init__(self, mac: str, controller: OmadaController, description: OmadaEntityDescription) -> None:

        self._mac = mac
        self.controller = controller
        self.entity_description = description

        self._attr_available = description.available_fn(controller, mac)
        self._attr_device_info = description.device_info_fn(
            controller.api, mac)
        self._attr_unique_id = description.unique_id_fn(mac, description.key)
        self._attr_name = description.name_fn(controller.api, mac, description.key)

        self.controller.entities[self.entity_description.domain][self.entity_description.key].add(self._mac)

    async def async_added_to_hass(self) -> None:
        for signal, method in (
            (self.controller.signal_options_update, self.options_updated),
            (self.controller.signal_update, self.async_update)
        ):
            self.async_on_remove(
                async_dispatcher_connect(self.hass, signal, method))

    async def async_will_remove_from_hass(self) -> None:
        self.controller.entities[self.entity_description.domain][self.entity_description.key].remove(
            self._mac)

    @callback
    async def async_update(self):
        self.async_write_ha_state()

    @callback
    async def options_updated(self):
        """Remove entity if options updated to disable entity type"""
        if not self.entity_description.allowed_fn(self.controller, self._mac):
            await self.remove()

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
                    == self.controller._config_entry.entry_id
                ]
            )
            != len(entries_for_device)
            and len(entries_for_device_from_this_config_entry) == 1
        ):
            dr.async_update_device(
                entity_entry.device_id,
                remove_config_entry_id=self.controller._config_entry.entry_id,
            )

        er.async_remove(self.entity_id)
