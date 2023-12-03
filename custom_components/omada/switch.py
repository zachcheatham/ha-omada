from __future__ import annotations

import logging

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Dict, Any

from homeassistant.components.switch import (
    DOMAIN, SwitchEntity, SwitchEntityDescription, SwitchDeviceClass)
from homeassistant.core import callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .controller import OmadaController
from .api.controller import Controller
from .const import DOMAIN as OMADA_DOMAIN
from .omada_entity import (OmadaEntity, OmadaEntityDescription, device_device_info_fn,
                           client_device_info_fn, unique_id_fn)

from .omada_controller_entity import (
    OmadaControllerEntity,
    OmadaControllerEntityDescription,
    device_info_fn as controller_device_info_fn,
    unique_id_fn as controller_unique_id_fn,
)

BLOCK_SWITCH = "block"
RADIO_2G_SWITCH = "2ghz_radio"
RADIO_5G_SWITCH = "5ghz_radio"
RADIO_6G_SWITCH = "6ghz_radio"
AI_OPTIMIZATION_SWITCH = "ai_optimization"

LOGGER = logging.getLogger(__name__)


def ssid_enabled_fn(api: Controller, mac: str, ssid: str):
    for ssid_override in api.devices[mac].ssid_overrides:
        if ssid_override["globalSsid"] == ssid:
            return ssid_override.get("ssidEnable", False)

    return False


def rf_planning_schedule_enabled_fn(api: Controller):
    rf_planning_state = api.rf_planning
    if rf_planning_state is not None:
        return rf_planning_state.schedule_enable
    else:
        return None


@callback
async def block_client_fn(api: Controller, mac: str, enabled: bool) -> None:
    await api.known_clients.async_set_block(mac, not enabled)


@callback
async def enable_2g_radio_fn(api: Controller, mac: str, enabled: bool) -> None:
    await api.devices.async_set_radio_enable(mac, 2, enabled)


@callback
async def enable_5g_radio_fn(api: Controller, mac: str, enabled: bool) -> None:
    await api.devices.async_set_radio_enable(mac, 5, enabled)


@callback
async def enable_6g_radio_fn(api: Controller, mac: str, enabled: bool) -> None:
    await api.devices.async_set_radio_enable(mac, 6, enabled)


@callback
async def enable_ssid_fn(api: Controller, mac: str, enabled: bool, ssid: str) -> None:
    await api.devices.async_set_ssid_enable(mac, api.devices[mac].ssid_overrides, api.devices[mac].wlan_id, ssid, enabled)


@callback
async def enable_rf_planning_schedule_fn(api: Controller, enabled: bool) -> None:
    await api.set_rf_planning_enable(enabled)


@dataclass
class OmadaSwitchEntityDescriptionMixin():
    control_fn: Callable[[Controller, str, bool], Coroutine[Any, Any, None]]
    is_on_fn: Callable[[Controller, str], bool]


@dataclass
class OmadaSwitchEntityDescription(
    OmadaEntityDescription,
    SwitchEntityDescription,
    OmadaSwitchEntityDescriptionMixin
):
    """Omada Switch Entity Description"""


@dataclass
class OmadaControllerSwitchEntityDescriptionMixin():
    control_fn: Callable[[Controller, str, bool], Coroutine[Any, Any, None]]
    is_on_fn: Callable[[Controller, str], bool]


@dataclass
class OmadaControllerSwitchEntityDescription(
    OmadaControllerEntityDescription,
    SwitchEntityDescription,
    OmadaControllerSwitchEntityDescriptionMixin
):
    """Omada Controller Switch Entity Description"""


CLIENT_ENTITY_DESCRIPTIONS: Dict[str, OmadaSwitchEntityDescription] = {
    BLOCK_SWITCH: OmadaSwitchEntityDescription(
        domain=DOMAIN,
        key=BLOCK_SWITCH,
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        has_entity_name=True,
        icon="mdi:network",
        allowed_fn=lambda controller, mac: (controller.option_track_clients and
                                            controller.option_client_block_switch and
                                            controller.is_client_allowed(mac)),
        supported_fn=lambda *_: True,
        available_fn=lambda controller, _: controller.available,
        device_info_fn=client_device_info_fn,
        name_fn=lambda *_: None,
        unique_id_fn=unique_id_fn,
        is_on_fn=lambda api, mac: not api.known_clients[mac].block,
        control_fn=block_client_fn
    )
}

DEVICE_ENTITY_DESCRIPTIONS: Dict[str, OmadaSwitchEntityDescription] = {
    RADIO_2G_SWITCH: OmadaSwitchEntityDescription(
        domain=DOMAIN,
        key=RADIO_2G_SWITCH,
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        has_entity_name=True,
        icon="mdi:antenna",
        allowed_fn=lambda controller, _: (controller.option_device_controls and
                                          controller.option_track_devices),
        supported_fn=lambda *_: True,
        available_fn=lambda controller, _: controller.available,
        device_info_fn=device_device_info_fn,
        name_fn=lambda *_: "2.4Ghz Radio",
        unique_id_fn=unique_id_fn,
        is_on_fn=lambda api, mac: api.devices[mac].radio_enabled_2ghz,
        control_fn=enable_2g_radio_fn
    ),
    RADIO_5G_SWITCH: OmadaSwitchEntityDescription(
        domain=DOMAIN,
        key=RADIO_5G_SWITCH,
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        has_entity_name=True,
        icon="mdi:antenna",
        allowed_fn=lambda controller, _: (controller.option_device_controls and
                                          controller.option_track_devices),
        supported_fn=lambda controller, mac: controller.api.devices[mac].supports_5ghz,
        available_fn=lambda controller, _: controller.available,
        device_info_fn=device_device_info_fn,
        name_fn=lambda *_: "5Ghz Radio",
        unique_id_fn=unique_id_fn,
        is_on_fn=lambda api, mac: api.devices[mac].radio_enabled_5ghz,
        control_fn=enable_5g_radio_fn
    ),
    RADIO_6G_SWITCH: OmadaSwitchEntityDescription(
        domain=DOMAIN,
        key=RADIO_6G_SWITCH,
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        has_entity_name=True,
        icon="mdi:antenna",
        allowed_fn=lambda controller, _: (controller.option_device_controls and
                                          controller.option_track_devices),
        supported_fn=lambda controller, mac: controller.api.devices[mac].supports_6ghz,
        available_fn=lambda controller, _: controller.available,
        device_info_fn=device_device_info_fn,
        name_fn=lambda *_: "6Ghz Radio",
        unique_id_fn=unique_id_fn,
        is_on_fn=lambda api, mac: api.devices[mac].radio_enabled_6ghz,
        control_fn=enable_6g_radio_fn
    )
}

CONTROLLER_ENTITY_DESCRIPTIONS: dict[
    str, OmadaControllerSwitchEntityDescription
] = {
    # AI_OPTIMIZATION_SWITCH: OmadaControllerSwitchEntityDescription(
    #     domain=DOMAIN,
    #     key=AI_OPTIMIZATION_SWITCH,
    #     device_class=SwitchDeviceClass.SWITCH,
    #     entity_category=EntityCategory.CONFIG,
    #     has_entity_name=True,
    #     icon="mdi:chart-box",
    #     available_fn=lambda controller: controller.available,
    #     device_info_fn=controller_device_info_fn,
    #     name_fn=lambda *_: "WLAN Optimization Schedule",
    #     unique_id_fn=controller_unique_id_fn,
    #     is_on_fn=rf_planning_schedule_enabled_fn,
    #     control_fn=enable_rf_planning_schedule_fn
    # )
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    controller: OmadaController = hass.data[OMADA_DOMAIN][config_entry.entry_id]

    # Set up Controller Entities
    for description in CONTROLLER_ENTITY_DESCRIPTIONS.values():
        entity = OmadaControllerSwitchEntity(controller, description)
        async_add_entities([entity])

    @callback
    def items_added() -> None:

        if controller.option_track_clients:
            controller.register_platform_entities(
                controller.api.clients,
                OmadaSwitchEntity,
                CLIENT_ENTITY_DESCRIPTIONS,
                async_add_entities)

        if controller.option_track_devices:
            device_descriptions: Dict[str, OmadaSwitchEntityDescription] = None

            if controller.option_device_controls:

                device_descriptions = DEVICE_ENTITY_DESCRIPTIONS.copy()

                # Add SSID switches
                for ssid in controller.api.ssids:
                    key = "ssid_{}".format(ssid.replace("-", "_"))
                    device_descriptions[key] = OmadaSwitchEntityDescription(
                        domain=DOMAIN,
                        key=key,
                        device_class=SwitchDeviceClass.SWITCH,
                        entity_category=EntityCategory.CONFIG,
                        has_entity_name=True,
                        icon="mdi:wifi",
                        allowed_fn=lambda controller, _, ssid=ssid: (controller.option_device_controls and
                                                                     controller.option_track_devices and
                                                                     ssid in controller.api.ssids),
                        supported_fn=lambda *_: True,
                        available_fn=lambda controller, _: controller.available,
                        device_info_fn=device_device_info_fn,
                        name_fn=lambda *_, ssid=ssid: f"{ssid} WLAN",
                        unique_id_fn=unique_id_fn,
                        is_on_fn=lambda api, mac, s=ssid: ssid_enabled_fn(
                            api, mac, s),
                        control_fn=lambda api, mac, enabled, s=ssid: enable_ssid_fn(
                            api, mac, enabled, s)
                    )

            else:
                device_descriptions = DEVICE_ENTITY_DESCRIPTIONS

            controller.register_platform_entities(
                controller.api.devices,
                OmadaSwitchEntity,
                device_descriptions,
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
            OmadaSwitchEntity,
            CLIENT_ENTITY_DESCRIPTIONS,
            config_entry,
            async_add_entities
        )

    items_added()


class OmadaSwitchEntity(OmadaEntity, SwitchEntity):

    entity_description: OmadaSwitchEntityDescription

    def __init__(self, mac: str, controller: OmadaController, description: OmadaEntityDescription) -> None:
        super().__init__(mac, controller, description)
        self._attr_is_on = self.entity_description.is_on_fn(
            controller.api, mac)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.entity_description.control_fn(self.controller.api, self._mac, True)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.entity_description.control_fn(self.controller.api, self._mac, False)
        self._attr_is_on = False
        self.async_write_ha_state()

    @callback
    async def async_update(self):

        if ((is_on := self.entity_description.is_on_fn(self.controller.api, self._mac)) != self.is_on):
            self._attr_is_on = is_on
            await super().async_update()


class OmadaControllerSwitchEntity(OmadaControllerEntity, SwitchEntity):
    controller: OmadaController
    entity_description: OmadaControllerSwitchEntityDescription

    def __init__(self, controller: OmadaController, description: OmadaControllerEntityDescription) -> None:
        super().__init__(controller, description)
        self._attr_is_on = self.entity_description.is_on_fn(controller.api)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.entity_description.control_fn(self.controller.api, True)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.entity_description.control_fn(self.controller.api, False)
        self._attr_is_on = False
        self.async_write_ha_state()

    @callback
    async def async_update(self):
        if ((is_on := self.entity_description.is_on_fn(self.controller.api)) != self.is_on):
            self._attr_is_on = is_on
            await super().async_update()
