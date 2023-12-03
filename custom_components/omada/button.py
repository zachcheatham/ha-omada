from __future__ import annotations

import logging

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.button import (
    DOMAIN,
    ButtonEntity,
    ButtonEntityDescription
)
from homeassistant.core import callback
from homeassistant.helpers.entity import EntityCategory

from .controller import OmadaController
from .api.controller import Controller

from .const import DOMAIN as OMADA_DOMAIN
from .omada_controller_entity import (
    OmadaControllerEntity,
    OmadaControllerEntityDescription,
    device_info_fn,
    unique_id_fn
)

AI_OPTIMIZATION_BUTTON = "ai_optimization"

LOGGER = logging.getLogger(__name__)

@callback
async def start_rf_planning_fn(api: Controller) -> None:
    await api.start_rf_planning()

@dataclass
class OmadaControllerButtonEntityDescriptionMixin:
    activate_fn: Callable[[OmadaController], None]


@dataclass
class OmadaControllerButtonEntityDescription(
    ButtonEntityDescription,
    OmadaControllerEntityDescription,
    OmadaControllerButtonEntityDescriptionMixin,
):
    """Omada Controller Button Entity Description"""

    pass


CONTROLLER_ENTITY_DESCRIPTIONS: dict[
    str, OmadaControllerButtonEntityDescription
] = {
    AI_OPTIMIZATION_BUTTON: OmadaControllerButtonEntityDescription(
        domain=DOMAIN,
        key=AI_OPTIMIZATION_BUTTON,
        entity_category=EntityCategory.DIAGNOSTIC,
        has_entity_name=True,
        icon="mdi:chart-box",
        available_fn=lambda controller: controller.available,
        device_info_fn=device_info_fn,
        name_fn=lambda *_: "Start WLAN Optimization",
        unique_id_fn=unique_id_fn,
        activate_fn=start_rf_planning_fn
    )
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    controller: OmadaController = hass.data[OMADA_DOMAIN][config_entry.entry_id]

    # Set up Controller Entities
    for description in CONTROLLER_ENTITY_DESCRIPTIONS.values():
        entity = OmadaControllerButtonEntity(controller, description)
        async_add_entities([entity])


class OmadaControllerButtonEntity(OmadaControllerEntity, ButtonEntity):
    controller: OmadaController
    entity_description: OmadaControllerButtonEntityDescription

    def __init__(
        self, controller: OmadaController, description: OmadaControllerEntityDescription
    ) -> None:

        super().__init__(controller, description)

    async def async_press(self) -> None:
        await self.entity_description.activate_fn(self.controller.api)
