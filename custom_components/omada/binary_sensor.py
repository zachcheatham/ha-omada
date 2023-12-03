from __future__ import annotations

import logging

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    DOMAIN,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import callback
from homeassistant.helpers.entity import EntityCategory

from .controller import OmadaController

from .const import DOMAIN as OMADA_DOMAIN
from .omada_controller_entity import (
    OmadaControllerEntity,
    OmadaControllerEntityDescription,
    device_info_fn,
    unique_id_fn,
)

AI_OPTIMIZATION_SENSOR = "ai_optimization"

LOGGER = logging.getLogger(__name__)


@callback
def rf_planning_state_value_fn(controller: OmadaController) -> bool | None:
    """Retrieve AI Optimization Status"""
    rf_planning_state = controller.api.rf_planning
    if rf_planning_state is not None:
        return rf_planning_state.status == 2
    else:
        return None


@dataclass
class OmadaControllerBinarySensorEntityDescriptionMixin:
    value_fn: Callable[[OmadaController], bool | None]


@dataclass
class OmadaControllerBinarySensorEntityDescription(
    BinarySensorEntityDescription,
    OmadaControllerEntityDescription,
    OmadaControllerBinarySensorEntityDescriptionMixin,
):
    """Omada Controller Binary Sensor Entity Description"""

    value_fn: Callable[[OmadaController], bool | None]


CONTROLLER_ENTITY_DESCRIPTIONS: dict[
    str, OmadaControllerBinarySensorEntityDescription
] = {
    AI_OPTIMIZATION_SENSOR: OmadaControllerBinarySensorEntityDescription(
        domain=DOMAIN,
        key=AI_OPTIMIZATION_SENSOR,
        entity_category=EntityCategory.DIAGNOSTIC,
        has_entity_name=True,
        icon="mdi:chart-box",
        available_fn=lambda controller: controller.available,
        device_info_fn=device_info_fn,
        name_fn=lambda *_: "WLAN Optimization Running",
        unique_id_fn=unique_id_fn,
        value_fn=rf_planning_state_value_fn,
    )
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    controller: OmadaController = hass.data[OMADA_DOMAIN][config_entry.entry_id]

    # Set up Controller Entities
    for description in CONTROLLER_ENTITY_DESCRIPTIONS.values():
        entity = OmadaControllerBinarySensorEntity(controller, description)
        async_add_entities([entity])


class OmadaControllerBinarySensorEntity(OmadaControllerEntity, BinarySensorEntity):
    controller: OmadaController
    entity_description: OmadaControllerBinarySensorEntityDescription

    def __init__(
        self, controller: OmadaController, description: OmadaControllerEntityDescription
    ) -> None:

        super().__init__(controller, description)

        self.update_value(force_update=True)

    def update_value(self, force_update=False) -> bool:
        """Update value. Returns true if state should update."""
        prev_value = self._attr_is_on
        next_value = self.entity_description.value_fn(self.controller)

        if prev_value != next_value:
            self._attr_is_on = next_value
            return True

        return False

    @callback
    async def async_update(self):
        if self.update_value():
            await super().async_update()
