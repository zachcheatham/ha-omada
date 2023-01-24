import logging
from datetime import datetime, timedelta

from homeassistant.components.switch import DOMAIN, SwitchEntity
from homeassistant.core import callback
from homeassistant.helpers import entity_registry
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_registry import async_entries_for_config_entry

from .controller import OmadaController
from .const import (DOMAIN as OMADA_DOMAIN)
from .omada_entity import OmadaClient

BLOCK_SWITCH = "block"

LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    controller: OmadaController = hass.data[OMADA_DOMAIN][config_entry.entry_id]
    controller.entities[DOMAIN] = {
        BLOCK_SWITCH: set()
    }

    er = entity_registry.async_get(hass)
    initial_client_set = controller.get_clients_filtered()

    # Add entries that used to exist in HA but are now disconnected.
    for entry in async_entries_for_config_entry(er, config_entry.entry_id):
        if entry.domain == DOMAIN:
            mac = entry.unique_id.split("-", 1)[1]

            if mac not in controller.api.devices:
                if mac not in controller.api.clients:
                    if mac in controller.api.known_clients:
                        initial_client_set.append(mac)

                # Remove entries that have moved to a filtered out ssid since restart
                elif controller.option_ssid_filter and controller.api.clients[mac].ssid not in controller.option_ssid_filter:
                    er.async_remove(entry.entity_id)

    @callback
    def items_added(clients: set = None) -> None:

        if controller.option_track_clients:
            if clients is None:
                clients = controller.get_clients_filtered()

            if controller.option_client_block_switch:
                add_block_entities(clients, controller, async_add_entities)

    for signal in (controller.signal_update, controller.signal_options_update):
        config_entry.async_on_unload(
            async_dispatcher_connect(hass, signal, items_added))

    items_added(initial_client_set)


@callback
def add_block_entities(clients: set, controller: OmadaController, async_add_entities):

    sensors = []

    for mac in clients:
        if mac not in controller.entities[DOMAIN][BLOCK_SWITCH]:
            sensors.append(OmadaClientBlockSwitch(controller, mac))

    if sensors:
        async_add_entities(sensors)


class OmadaClientBlockSwitch(OmadaClient, SwitchEntity):

    DOMAIN = DOMAIN
    TYPE = BLOCK_SWITCH

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, controller: OmadaController, mac: str) -> None:
        super().__init__(controller, mac)

        self._is_blocked = self.client_blocked
    
    @callback
    async def async_update(self) -> None:
        if self._is_blocked != self.client_blocked:
            self._is_blocked = self.client_blocked
            await super().async_update()
    
    async def async_turn_on(self, **kwargs):
        await self._controller.api.known_clients.async_set_block(self.key, False)
        self._is_blocked = False
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self._controller.api.known_clients.async_set_block(self.key, True)
        self._is_blocked = True
        self.async_write_ha_state()

    @property
    def is_on(self):
        return not self._is_blocked

    @property
    def client_blocked(self):
        return self._controller.api.known_clients[self.key].block

    @property
    def icon(self):
        if self.is_on:
            return "mdi:network"
        return "mdi:network-off"
        
    @callback
    async def options_updated(self):
        if not self._controller.option_client_block_switch:
            await self.remove()
        else:
            await super().options_updated()
