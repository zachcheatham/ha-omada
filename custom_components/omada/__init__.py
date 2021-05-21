import logging

from homeassistant.core import HomeAssistant
from custom_components.omada.controller import OmadaController
from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from .const import DATA_OMADA, DOMAIN

LOGGER = logging.getLogger(__name__)

PLATFORMS = ["device_tracker"]

async def async_setup(hass, config):
    conf = config.get(DOMAIN)
    if conf is None:
        return True

    domains_list = hass.config_entries.async_domains()
    if DOMAIN in domains_list:
        return True

    hass.async_create_task(
        hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_IMPORT}, data=conf)
    )

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):

    controller = OmadaController(hass, entry)
    await controller.async_setup()

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_OMADA: controller
    }

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    controller = hass.data[DOMAIN].pop(entry.entry_id)[DATA_OMADA]
    return await controller.async_close()

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    pass
    # Recreate controller object with new options

