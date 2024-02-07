from __future__ import annotations

import logging
import time

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Dict, Mapping

from homeassistant.components.device_tracker import DOMAIN
from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.components.device_tracker.const import SourceType
from homeassistant.core import callback
from homeassistant.helpers import device_registry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .api.controller import Controller
from .api.clients import Client
from .const import DOMAIN as OMADA_DOMAIN
from .controller import OmadaController
from .omada_entity import (OmadaEntity, OmadaEntityDescription, client_device_info_fn,
                           device_device_info_fn)

LOGGER = logging.getLogger(__name__)

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

CONNECTED_WIRED_CLIENT_ATTRIBUTES = (
    "name",
    "hostname",
    "ip",
    "mac",
    "wireless",
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

@callback
def client_name_fn(api: Controller, mac: str, _) -> str:
    if mac in api.known_clients:
        return api.known_clients[mac].name
    else:
        return mac

@callback
def client_connected_fn(controller: OmadaController, mac: str) -> bool:
    """Retrieve if clients are connected if they are currently connected to an AP or if they were last connected in the last option_disconnect_timeout minutes"""
    return (mac in controller.api.clients or
            (mac in controller.api.known_clients and
             controller.option_disconnect_timeout is not None and
             controller.api.known_clients[mac].last_seen > (time.time() * 1000) - (controller.option_disconnect_timeout * 60000)))


@callback
def client_attributes_fn(controller: OmadaController, mac: str) -> bool:
    """Retrieve extra attributes for clients"""

    attributes = {}

    target_attrs = []
    client: Client = None

    if mac in controller.api.clients:
        client = controller.api.clients[mac]
        if client.wireless:
            target_attrs = CONNECTED_CLIENT_ATTRIBUTES
        else:
            target_attrs = CONNECTED_WIRED_CLIENT_ATTRIBUTES
    elif mac in controller.api.known_clients:
        target_attrs = DISCONNECTED_CLIENT_ATTRIBUTES
        client = controller.api.known_clients[mac]

    for k in target_attrs:
        if hasattr(client, k) and getattr(client, k):
            if k in ["mac", "ap_mac"]:
                attributes[k] = device_registry.format_mac(
                    getattr(client, k))
            else:
                attributes[k] = getattr(client, k)

    return attributes

@callback
def device_name_fn(api: Controller, mac: str, _) -> str:
    if mac in api.devices:
        return api.devices[mac].name
    else:
        return mac

@callback
def device_connected_fn(controller: OmadaController, mac: str) -> bool:
    """Retrieve if a device is connected."""
    return (mac in controller.api.devices and
            controller.api.devices[mac].status_category == 1)

@callback
def device_attributes_fn(controller: OmadaController, mac: str) -> bool:
    """Retrieve extra device attributes"""
    device = controller.api.devices[mac]

    attributes = {}
    for k in DEVICE_ATTRIBUTES:
        if hasattr(device, k) and getattr(device, k):
            if k == "mac":
                attributes[k] = device_registry.format_mac(
                    getattr(device, k))
            else:
                attributes[k] = getattr(device, k)

    return attributes

@dataclass
class OmadaDeviceTrackerEntityDescriptionMixin():
    connected_fn: Callable[[OmadaController, str], bool]
    extra_attributes_fn: Callable[[
        OmadaController, str], Mapping[str, Any] | None]


@dataclass
class OmadaDeviceTrackerEntityDescription(
    OmadaEntityDescription,
    OmadaDeviceTrackerEntityDescriptionMixin
):
    """Omada device tracker entity description"""
    domain = DOMAIN


CLIENT_ENTITY_DESCRIPTIONS: Dict[str, OmadaDeviceTrackerEntityDescription] = {
    CLIENT_TRACKER: OmadaDeviceTrackerEntityDescription(
        domain=DOMAIN,
        key=CLIENT_TRACKER,
        allowed_fn=lambda controller, mac: (controller.option_track_clients and
                                            controller.is_client_allowed(mac)),
        supported_fn=lambda *_: True,
        available_fn=lambda controller, _: controller.available,
        device_info_fn=client_device_info_fn,
        name_fn=client_name_fn,
        unique_id_fn=lambda mac, _: mac,
        connected_fn=client_connected_fn,
        extra_attributes_fn=client_attributes_fn
    )
}


DEVICE_ENTITY_DESCRIPTIONS: Dict[str, OmadaDeviceTrackerEntityDescription] = {
    DEVICE_TRACKER: OmadaDeviceTrackerEntityDescription(
        domain=DOMAIN,
        key=DEVICE_TRACKER,
        allowed_fn=lambda controller, _: controller.option_track_devices,
        supported_fn=lambda *_: True,
        available_fn=lambda controller, _: controller.available,
        device_info_fn=device_device_info_fn,
        name_fn=device_name_fn,
        unique_id_fn=lambda mac, _: mac,
        connected_fn=device_connected_fn,
        extra_attributes_fn=device_attributes_fn
    )
}



async def async_setup_entry(hass, config_entry, async_add_entities):
    controller: OmadaController = hass.data[OMADA_DOMAIN][config_entry.entry_id]

    @callback
    def items_added() -> None:

        if controller.option_track_clients:
            controller.register_platform_entities(
                controller.api.clients,
                OmadaDeviceTrackerEntity,
                CLIENT_ENTITY_DESCRIPTIONS,
                async_add_entities)

        if controller.option_track_devices:
            controller.register_platform_entities(
                controller.api.devices,
                OmadaDeviceTrackerEntity,
                DEVICE_ENTITY_DESCRIPTIONS,
                async_add_entities)

    for signal in (controller.signal_update, controller.signal_options_update):
        config_entry.async_on_unload(
            async_dispatcher_connect(hass, signal, items_added))

    if controller.option_track_clients:
        controller.restore_cleanup_platform_entities(
            DOMAIN,
            controller.api.clients,
            controller.api.known_clients,
            controller.api.devices,
            OmadaDeviceTrackerEntity,
            CLIENT_ENTITY_DESCRIPTIONS,
            config_entry,
            async_add_entities,
            CLIENT_TRACKER
        )

    items_added()

class OmadaDeviceTrackerEntity(OmadaEntity, ScannerEntity):

    entity_description: OmadaDeviceTrackerEntityDescription

    @property
    def is_connected(self) -> bool:
        return self.entity_description.connected_fn(self.controller, self._mac)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        return self.entity_description.extra_attributes_fn(self.controller, self._mac)

    @property
    def unique_id(self) -> str | None:
        return self.entity_description.unique_id_fn(self._mac, self.entity_description.key)

    @property
    def device_info(self) -> DeviceInfo | None:
        return self.entity_description.device_info_fn(self.controller.api, self._mac)

    @property
    def source_type(self) -> str:
        return SourceType.ROUTER
