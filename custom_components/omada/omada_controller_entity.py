from __future__ import annotations

import logging

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.core import callback
from homeassistant.helpers.entity import Entity, EntityDescription, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import ATTR_MANUFACTURER as ATTR_OMADA_MANUFACTURER, ATTR_CONTROLLER_MODEL, DOMAIN
from .api.controller import Controller

if TYPE_CHECKING:
    from .controller import OmadaController


LOGGER = logging.getLogger(__name__)

@callback
def entity_available_fn(controller: OmadaController) -> bool:
    return controller.available


@callback
def device_info_fn(api: Controller) -> DeviceInfo:
    return DeviceInfo(
        manufacturer=ATTR_OMADA_MANUFACTURER,
        identifiers={(DOMAIN, api.controller_id)},
        model=ATTR_CONTROLLER_MODEL,
        sw_version=api.version,
        name=api.name,
    )

@callback
def unique_id_fn(controller: OmadaController, entity_type: str) -> str:
    return f"{entity_type}-{controller.api.controller_id}"


@dataclass
class OmadaControllerDescriptionMixin():
    domain: str
    available_fn: Callable[[OmadaController], bool]
    device_info_fn: Callable[[Controller], bool]
    name_fn: Callable[[Controller, str], str]
    unique_id_fn: Callable[[OmadaController], str]


@dataclass
class OmadaControllerEntityDescription(EntityDescription, OmadaControllerDescriptionMixin):
    """Omada enitty description"""


class OmadaControllerEntity(Entity):

    entity_description: OmadaControllerEntityDescription

    _attr_should_poll = False
    _attr_unique_id: str

    def __init__(self, controller: OmadaController, description: OmadaControllerEntityDescription) -> None:

        self.controller = controller
        self.entity_description = description

        self._attr_available = description.available_fn(controller)
        self._attr_device_info = description.device_info_fn(controller.api)
        self._attr_unique_id = description.unique_id_fn(self.controller, description.key)
        self._attr_name = description.name_fn(controller.api, description.key)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(self.hass, self.controller.signal_update, self.async_update))

    @callback
    async def async_update(self):
        self.async_write_ha_state()
