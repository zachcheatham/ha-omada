from custom_components.omada.api.clients import Client
from homeassistant.helpers.entity_registry import async_entries_for_config_entry
from custom_components.omada import LOGGER
from homeassistant.components.device_tracker.const import SOURCE_TYPE_ROUTER
from homeassistant.core import callback
from custom_components.omada.api.controller import Controller
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from homeassistant.components.device_tracker import (
    DOMAIN,
    PLATFORM_SCHEMA
)
from homeassistant.components.device_tracker.config_entry import ScannerEntity

from homeassistant.const import (
    CONF_URL, CONF_USERNAME, CONF_PASSWORD, CONF_VERIFY_SSL
)

from .controller import OmadaController
from .const import (CONF_SSID_FILTER, CONF_SITE, DATA_OMADA, DOMAIN as OMADA_DOMAIN)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): cv.string,
    vol.Optional(CONF_SITE, default="Default"): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_SSID_FILTER, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_VERIFY_SSL, default=True): cv.boolean
})

CONNECTED_ATTRIBUTES = (
    "ip",
    "wireless",
    "ssid",
    "ap_mac",
    "signal_level",
    "rssi",
    "uptime",
    "guest"
)

DISCONNECTED_ATTRIBUTES = (
    "wireless",
    "guest",
    "last_seen"
)

async def async_setup_entry(hass, config_entry, async_add_entities):

    controller: OmadaController = hass.data[OMADA_DOMAIN][config_entry.entry_id][DATA_OMADA]
    controller.entities[DOMAIN] = set()

    def get_clients_filtered():
        clients = set()
        
        for mac in controller.api.clients:
            client = controller.api.clients[mac]

            # Skip adding client if not connected to ssid in filter list
            if controller.option_ssid_filter and client.ssid not in controller.option_ssid_filter:
                continue

            clients.add(client.mac)

        return clients

    @callback
    def items_added(clients: set = get_clients_filtered()):
        add_client_entities(controller, async_add_entities, clients)

    config_entry.async_on_unload(
        async_dispatcher_connect(hass, controller.signal_update, items_added)
    )

    entity_registry = await hass.helpers.entity_registry.async_get_registry()
    initial_clients=set()

    # Add connected entries
    for mac in get_clients_filtered():
        initial_clients.add(mac)

    # Add entries that used to exist in HA but are now disconnected.
    for entry in async_entries_for_config_entry(entity_registry, config_entry.entry_id):
        mac = entry.unique_id
        
        if mac not in controller.api.clients:
            if mac in controller.api.known_clients:
                initial_clients.add(mac)
        elif controller.option_ssid_filter and controller.api.clients[mac].ssid not in controller.option_ssid_filter:
            entity_registry.async_remove(entry.entity_id)

    items_added(initial_clients)


@callback
def add_client_entities(controller: Controller, async_add_entities, clients):
    trackers = []

    for mac in clients:
        if mac in controller.entities[DOMAIN]:
            continue

        trackers.append(OmadaClientTracker(controller, mac))

    if trackers:
        async_add_entities(trackers)

class OmadaClientTracker(ScannerEntity):

    DOMAIN = DOMAIN

    def __init__(self, controller: OmadaController, mac):
        self._controller = controller
        self._mac = mac
        self._controller.entities[DOMAIN].add(mac)

    @callback
    def async_update_callback(self):
        super().async_update_callback()

    @property
    def unique_id(self) -> str:
        return self._mac

    @property
    def name(self) -> str:
        return f"client_{self._controller.api.known_clients[self._mac].name}"

    @property
    def is_connected(self) -> bool:
        return self._mac in self._controller.api.clients

    @property
    def extra_state_attributes(self):

        if self.is_connected:
            client=self._controller.api.clients[self._mac]
            return {
                k: getattr(client, k) for k in CONNECTED_ATTRIBUTES
            }
        elif self._mac in self._controller.api.known_clients:
            client=self._controller.api.known_clients[self._mac]
            return {
                k: getattr(client, k) for k in DISCONNECTED_ATTRIBUTES
            }
        else:
            None

    @property
    def source_type(self) -> str:
        return SOURCE_TYPE_ROUTER

    @property
    def should_poll(self) -> bool:
        return False

    async def remove(self):
        entity_registry = await self.hass.helpers.entity_registry.async_get_registry()

        await self.async_remove()
        entity_registry.async_remove(self.entity_id)

    @callback
    async def async_update(self):
        if (self._controller.option_ssid_filter
        and self.is_connected
        and self._controller.api.clients[self._mac].ssid not in self._controller.option_ssid_filter):
            
            await self.remove()
        else:
            self.async_write_ha_state()

    async def options_updated(self):
        if (self._controller.option_ssid_filter
        and self.is_connected
        and self._controller.api.clients[self._mac].ssid not in self._controller.option_ssid_filter):

            await self.remove()

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                self._controller.signal_update,
                self.async_update,
            )
        )

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                self._controller.signal_options_update,
                self.options_updated,
            )
        )
