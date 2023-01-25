import logging
import time

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.device_tracker import (DOMAIN, PLATFORM_SCHEMA)
from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.components.device_tracker.const import SOURCE_TYPE_ROUTER
from homeassistant.const import CONF_URL, CONF_USERNAME, CONF_PASSWORD, CONF_VERIFY_SSL
from homeassistant.core import callback
from homeassistant.helpers import device_registry, entity_registry
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_registry import async_entries_for_config_entry
from homeassistant.helpers.entity import DeviceInfo

from .const import (CONF_SSID_FILTER, CONF_SITE, CONF_DISCONNECT_TIMEOUT,
                    DOMAIN as OMADA_DOMAIN, ATTR_MANUFACTURER as ATTR_OMADA_MANUFACTURER)
from .controller import OmadaController
from .omada_entity import OmadaClient, OmadaDevice

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

CLIENT_TRACKER = "client"
DEVICE_TRACKER = "device"

CONNECTED_CLIENT_ATTRIBUTES = (
    "name",
    "hostname",
    "ip",
    "mac",
    "wireless",
    "ssid",
    "ap_mac",
    "ap_name",
    "channel",
    "radio",
    "wifi_mode",
    "signal_level",
    "rssi",
    "power_save",
    "guest"
)

DISCONNECTED_CLIENT_ATTRIBUTES = (
    "name",
    "mac",
    "wireless",
    "guest",
    "last_seen"
)

DEVICE_ATTRIBUTES = [
    "type",
    "model",
    "firmware",
    "status",
    "status_category",
    "mesh",
    "supports_5ghz",
    "supports_6ghz"
    "radio_mode_2ghz",
    "radio_mode_5ghz",
    "radio_mode_6ghz",
    "bandwidth_2ghz",
    "bandwidth_5ghz",
    "bandwidth_6ghz",
    "tx_power_2ghz",
    "tx_power_5ghz",
    "tx_power_6ghz",
]

async def async_setup_entry(hass, config_entry, async_add_entities):
    controller: OmadaController = hass.data[OMADA_DOMAIN][config_entry.entry_id]
    controller.entities[DOMAIN] = {CLIENT_TRACKER: set(), DEVICE_TRACKER: set()}

    @callback
    def items_added(clients: set = None, devices: set = None) -> None:
        
        if controller.option_track_clients:
            if clients is None:
                clients = controller.get_clients_filtered()
            add_client_entities(controller, async_add_entities, clients)

        if controller.option_track_devices:
            if devices is None:
                devices = controller.api.devices

            add_device_entities(controller, async_add_entities, devices)

    config_entry.async_on_unload(
        async_dispatcher_connect(hass, controller.signal_update, items_added)
    )

    er = entity_registry.async_get(hass)
    initial_client_set = controller.get_clients_filtered()

    # Add entries that used to exist in HA but are now disconnected.
    for entry in async_entries_for_config_entry(er, config_entry.entry_id):
        if entry.domain == DOMAIN:
            mac = entry.unique_id

            if mac not in controller.api.devices:
                if mac not in controller.api.clients:
                    if mac in controller.api.known_clients:
                        initial_client_set.append(mac)

                # Remove entry if it became apart of an SSID that is filtered out
                elif controller.option_ssid_filter and controller.api.clients[mac].ssid not in controller.option_ssid_filter:
                    er.async_remove(entry.entity_id)

    items_added(initial_client_set)


@callback
def add_client_entities(controller: OmadaController, async_add_entities, macs):
    trackers = []

    for mac in macs:
        if mac not in controller.entities[DOMAIN][OmadaClientTracker.TYPE]:
            trackers.append(OmadaClientTracker(controller, mac))

    if trackers:
        async_add_entities(trackers)

@callback
def add_device_entities(controller: OmadaController, async_add_entities, macs):
    trackers = []

    for mac in macs:
        if mac not in controller.entities[DOMAIN][OmadaDeviceTracker.TYPE]:
            trackers.append(OmadaDeviceTracker(controller, mac))

    if trackers:
        async_add_entities(trackers)


class OmadaClientTracker(OmadaClient, ScannerEntity):

    DOMAIN = DOMAIN
    TYPE = CLIENT_TRACKER

    @property
    def is_connected(self) -> bool:
        # Connected if mac is present in clients dict or if mac is previously known and was last connected in the last self._disconnect_timeout minutes
        return (self._mac in self._controller.api.clients or
                (self._mac in self._controller.api.known_clients and
                 self._controller.option_disconnect_timeout is not None and
                 self._controller.api.known_clients[self._mac].last_seen > (time.time() * 1000) - (self._controller.option_disconnect_timeout * 60000)))

    @property
    def extra_state_attributes(self):
        attributes = {}

        target_attrs = []
        client = None

        if self._mac in self._controller.api.clients:
            target_attrs = CONNECTED_CLIENT_ATTRIBUTES
            client = self._controller.api.clients[self._mac]
        elif self._mac in self._controller.api.known_clients:
            target_attrs = DISCONNECTED_CLIENT_ATTRIBUTES
            client = self._controller.api.known_clients[self._mac]

        for k in target_attrs:
            if hasattr(client, k) and getattr(client, k):
                if k in ["mac", "ap_mac"]:
                    attributes[k] = device_registry.format_mac(
                        getattr(client, k))
                else:
                    attributes[k] = getattr(client, k)

        return attributes

    @property
    def source_type(self) -> str:
        return SOURCE_TYPE_ROUTER
    
    @property
    def unique_id(self) -> str:
        return self.key


class OmadaDeviceTracker(OmadaDevice, ScannerEntity):
    DOMAIN = DOMAIN
    TYPE = DEVICE_TRACKER

    @property
    def is_connected(self):
        return (self.key in self._controller.api.devices and 
            self._controller.api.devices[self.key].status_category == 1)
    

    @property
    def source_type(self) -> str:
        return SOURCE_TYPE_ROUTER
    
    @property
    def unique_id(self) -> str:
        return self.key
    
    @property
    def device_info(self):
        device = self._controller.api.devices[self.key]

        return DeviceInfo(
            connections={(CONNECTION_NETWORK_MAC, self.key)},
            manufacturer=ATTR_OMADA_MANUFACTURER,
            model=device.model,
            sw_version=device.firmware,
            name=device.name,
        )
    
    async def async_update_device_registry(self) -> None:
        dr = device_registry.async_get(self.hass)
        dr.async_get_or_create(
            config_entry_id=self._controller.config_entry.entry_id, **self.device_info
        )
    
    @property
    def extra_state_attributes(self):
        device = self._controller.api.devices[self.key]

        attributes = {}
        for k in DEVICE_ATTRIBUTES:
            if hasattr(device, k) and getattr(device, k):
                if k == "mac":
                    attributes[k] = device_registry.format_mac(getattr(device, k))
                else:
                    attributes[k] = getattr(device, k)

        return attributes

    @callback
    async def options_updated(self):
        pass
