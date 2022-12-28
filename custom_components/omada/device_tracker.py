import logging
import time

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.device_tracker import (DOMAIN, PLATFORM_SCHEMA)
from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.components.device_tracker.const import SOURCE_TYPE_ROUTER
from homeassistant.const import (CONF_URL, CONF_USERNAME, CONF_PASSWORD, CONF_VERIFY_SSL)
from homeassistant.core import callback
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_registry import async_entries_for_config_entry

from .const import (CONF_SSID_FILTER, CONF_SITE, CONF_DISCONNECT_TIMEOUT,
                    DATA_OMADA, DOMAIN as OMADA_DOMAIN)
from .controller import OmadaController

LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): cv.string,
    vol.Optional(CONF_SITE, default="Default"): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_SSID_FILTER, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_VERIFY_SSL, default=True): cv.boolean,
    vol.Optional(CONF_DISCONNECT_TIMEOUT, default=0): cv.positive_int
})


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

    def get_devices():
        devices = set()

        for mac in controller.api.devices:
            device = controller.api.devices[mac]
            devices.add(device.mac)

        return devices

    @callback
    def items_added(macs=None):
        if macs is None:
            macs = get_clients_filtered()
        add_client_entities(controller, async_add_entities, macs)

    config_entry.async_on_unload(
        async_dispatcher_connect(hass, controller.signal_update, items_added)
    )

    entity_registry = hass.helpers.entity_registry.async_get(hass)
    initial_set = set()

    # Add connected entries
    for mac in get_devices():
        initial_set.add(mac)
    for mac in get_clients_filtered():
        initial_set.add(mac)

    # Add entries that used to exist in HA but are now disconnected.
    for entry in async_entries_for_config_entry(entity_registry, config_entry.entry_id):
        mac = entry.unique_id

        if mac in controller.api.devices:
            continue
        elif mac not in controller.api.clients:
            if mac in controller.api.known_clients:
                initial_set.add(mac)
        elif controller.option_ssid_filter and controller.api.clients[mac].ssid not in controller.option_ssid_filter:
            entity_registry.async_remove(entry.entity_id)

    items_added(initial_set)


@callback
def add_client_entities(controller: OmadaController, async_add_entities, macs):
    trackers = []

    for mac in macs:
        if mac in controller.entities[DOMAIN]:
            continue

        if mac in controller.api.devices:
            trackers.append(OmadaDeviceTracker(controller, mac))
        else:
            trackers.append(OmadaClientTracker(controller, mac))

    if trackers:
        async_add_entities(trackers)


class OmadaClientTracker(ScannerEntity):
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
        if self._mac in self._controller.api.known_clients:
            return self._controller.api.known_clients[self._mac].name
        else:
            return self._mac

    @property
    def is_connected(self) -> bool:
        # Connected if mac is present in clients dict or if mac is previously known and was last connected in the last self._disconnect_timeout minutes
        return (self._mac in self._controller.api.clients or
                (self._mac in self._controller.api.known_clients and
                 self._controller.option_disconnect_timeout is not None and
                 self._controller.api.known_clients[self._mac].last_seen > (time.time() * 1000) - (self._controller.option_disconnect_timeout * 60000)))

    @property
    def extra_state_attributes(self):

        if self._mac in self._controller.api.clients:
            client = self._controller.api.clients[self._mac]
            return {
                k: getattr(client, k) for k in self.CONNECTED_ATTRIBUTES
            }
        elif self._mac in self._controller.api.known_clients:
            client = self._controller.api.known_clients[self._mac]
            return {
                k: getattr(client, k) for k in self.DISCONNECTED_ATTRIBUTES
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
        entity_registry = self.hass.helpers.entity_registry.async_get(self.hass)

        await self.async_remove()
        entity_registry.async_remove(self.entity_id)

    @callback
    async def async_update(self):
        if (self._controller.option_ssid_filter
                and self._mac in self._controller.api.clients
                and self._controller.api.clients[self._mac].ssid not in self._controller.option_ssid_filter):

            await self.remove()
        else:
            self.async_write_ha_state()

    async def options_updated(self):
        if (self._controller.option_ssid_filter
                and self._mac in self._controller.api.clients
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


class OmadaDeviceTracker(ScannerEntity):
    DOMAIN = DOMAIN

    ATTRIBUTES = [
        "type",
        "model",
        "firmware",
        "firmware_upgrade",
        "status",
        "status_category",
        "clients",
        "users",
        "guests",
        "cpu",
        "memory",
        "download",
        "upload",
        "tx_rate",
        "rx_rate",
        "mesh",
    ]

    def __init__(self, controller: OmadaController, mac):
        self._controller = controller
        self._mac = mac
        self._controller.entities[DOMAIN].add(mac)

    @callback
    def async_update_callback(self):
        super().async_update_callback()

    @property
    def unique_id(self) -> str:
        return format_mac(self._mac)

    @property
    def device_info(self):
        device = self._controller.api.devices[self._mac]
        return {
            # Serial numbers are unique identifiers within a specific domain
            "identifiers": {(self.DOMAIN, self.unique_id)},
            "name": self.name,
            "site": self.site,
            "default_manufacturer": "TP-Link",
            "type": getattr(device, "type"),
            "model": f"{getattr(device, 'model')} ",
            "sw_version": getattr(device, "firmware"),
            "suggested_area": "Network",
        }

    @property
    def name(self) -> str:
        name = self._controller.api.devices[self._mac].name

        return f"[{self.site.title()}] {name.title()}"

    @property
    def is_connected(self) -> bool:
        return self._controller.api.devices[self._mac].status_category == 1

    @property
    def ip_address(self) -> str:
        return self._controller.api.devices[self._mac].ip

    @property
    def mac_address(self) -> str:
        return format_mac(self._mac)

    @property
    def hostname(self) -> str:
        return self._controller.api.devices[self._mac].name

    @property
    def extra_state_attributes(self):
        device = self._controller.api.devices[self._mac]

        attributes = {}
        for k in self.ATTRIBUTES:
            if hasattr(device, k) and getattr(device, k):
                attributes[k] = getattr(device, k)

        return attributes

    @property
    def source_type(self) -> str:
        return SOURCE_TYPE_ROUTER

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def site(self) -> str:
        site = self._controller.api.site

        # Replace default site name if not set
        if site == "Default":
            site = "Omada"

        return site

    async def remove(self):
        entity_registry = self.hass.helpers.entity_registry.async_get(self.hass)

        await self.async_remove()
        entity_registry.async_remove(self.entity_id)

    @callback
    async def async_update(self):
        self.async_write_ha_state()

    async def options_updated(self):
        pass

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
