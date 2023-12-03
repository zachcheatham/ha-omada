from __future__ import annotations

import logging

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Dict

from homeassistant.components.update import (DOMAIN,
                                             UpdateDeviceClass, UpdateEntity, UpdateEntityFeature, UpdateEntityDescription)
from homeassistant.core import callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .controller import OmadaController
from .api.controller import Controller

from .const import (DOMAIN as OMADA_DOMAIN)
from .omada_entity import (OmadaEntity, OmadaEntityDescription, device_device_info_fn,
                           unique_id_fn)

LOGGER = logging.getLogger(__name__)


async def update_device_fn(controller: Controller, mac: str) -> None:
    await controller.devices.trigger_update(mac)

@dataclass
class OmadaUpdateEntityDescriptionMixin():
    version_fn: Callable[[Controller, str], str]
    latest_version_fn: Callable[[Controller, str], str]
    latest_version_rn_fn: Callable[[Controller, str], str]
    updating_fn: Callable[[Controller, str], bool]
    update_fn: Callable[[Controller, str], None]


@dataclass
class OmadaUpdateEntityDescription(
    UpdateEntityDescription,
    OmadaEntityDescription,
    OmadaUpdateEntityDescriptionMixin
):
    """Omada Update Entity Description"""


DEVICE_ENTITY_DESCRIPTIONS: Dict[str, OmadaUpdateEntityDescription] = {
    DOMAIN: OmadaUpdateEntityDescription(
        domain=DOMAIN,
        key=DOMAIN,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=UpdateDeviceClass.FIRMWARE,
        has_entity_name=True,
        allowed_fn=lambda controller, _: controller.option_track_devices,
        supported_fn=lambda *_: True,
        available_fn=lambda controller, _: controller.available,
        device_info_fn=device_device_info_fn,
        name_fn=lambda *_: " Firmware Update",
        unique_id_fn=unique_id_fn,
        version_fn=lambda controller, mac: controller.devices[mac].firmware,
        latest_version_fn=lambda controller, mac: controller.devices[mac].firmware_upgrade and controller.devices[mac].firmware_latest or controller.devices[mac].firmware,
        latest_version_rn_fn=lambda controller, mac: controller.devices[mac].firmware_upgrade and controller.devices[mac].firmware_latest_rn or None,
        updating_fn=lambda controller, mac: controller.devices[mac].status == 12,
        update_fn=update_device_fn
    )
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    controller: OmadaController = hass.data[OMADA_DOMAIN][config_entry.entry_id]

    @callback
    def items_added() -> None:

        if controller.option_track_devices:
            controller.register_platform_entities(
                controller.api.devices,
                OmadaUpdateEntity,
                DEVICE_ENTITY_DESCRIPTIONS,
                async_add_entities)

    for signal in (controller.signal_update, controller.signal_options_update):
        config_entry.async_on_unload(
            async_dispatcher_connect(hass, signal, items_added))

    items_added()


class OmadaUpdateEntity(OmadaEntity, UpdateEntity):

    entity_description: OmadaUpdateEntityDescription

    _attr_supported_features = (UpdateEntityFeature.RELEASE_NOTES | UpdateEntityFeature.PROGRESS | UpdateEntityFeature.INSTALL)

    def __init__(self, mac: str, controller: OmadaController, description: OmadaEntityDescription) -> None:

        super().__init__(mac, controller, description)
        self._attr_installed_version = self.entity_description.version_fn(
            controller.api, mac)
        self._attr_latest_version = self.entity_description.latest_version_fn(
            controller.api, mac)

    @callback
    async def async_update(self):

        upd = False

        if ((version := self.entity_description.version_fn(self.controller.api, self._mac)) != self._attr_installed_version):
            self._attr_installed_version = version
            upd = True

        if ((latest_version := self.entity_description.latest_version_fn(self.controller.api, self._mac)) != self._attr_latest_version):
            self._attr_latest_version = latest_version
            upd = True

        if ((progress := self.entity_description.updating_fn(self.controller.api, self._mac)) != self._attr_in_progress):
            self._attr_in_progress = progress
            upd = True

        if upd:
            await super().async_update()

    async def async_install(self, version: str | None, backup: bool, **kwargs: Any) -> None:
        await self.entity_description.update_fn(self.controller.api, self._mac)

    def release_notes(self) -> str | None:
        return self.entity_description.latest_version_rn_fn(self.controller.api, self._mac)
