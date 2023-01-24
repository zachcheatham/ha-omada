import logging

from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .controller import OmadaController

LOGGER = logging.getLogger(__name__)

PLATFORMS = ["device_tracker", "sensor", "switch"]


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
    omada_controller = OmadaController(hass, entry)
    await omada_controller.async_setup()

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = omada_controller

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    omada_controller = hass.data[DOMAIN].pop(entry.entry_id)
    return await omada_controller.async_close()


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    pass
