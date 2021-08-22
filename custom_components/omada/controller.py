
from datetime import timedelta
import logging

from aiohttp import CookieJar
import async_timeout
import ssl
from homeassistant.core import CALLBACK_TYPE, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval

from .api.controller import Controller
from .api.errors import (LoginFailed, OmadaApiException, RequestError, LoginRequired)

from .errors import (AuthenticationRequired, CannotConnect)

from .const import (
    CONF_SITE,
    CONF_SSID_FILTER,
    DATA_OMADA,
    DOMAIN as OMADA_DOMAIN
)

from homeassistant.components.device_tracker import DOMAIN

from homeassistant.const import (
    CONF_PASSWORD,
    CONF_URL,
    CONF_USERNAME,
    CONF_VERIFY_SSL
)
from homeassistant.helpers import aiohttp_client
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.entity_registry import async_entries_for_config_entry

SCAN_INTERVAL = timedelta(seconds=30) # TODO Remove after websockets

LOGGER = logging.getLogger(__name__)

class OmadaController:

    def __init__(self, hass, config_entry):
        self.hass = hass
        self._config_entry = config_entry
        self.api: Controller = None
        self.entities = {}
        self._on_close = []
        self.option_ssid_filter = None

        self.load_config_entry_options()

    def load_config_entry_options(self):
        options = self._config_entry.options

        self.option_ssid_filter = set(options.get(CONF_SSID_FILTER, []))

    @property
    def username(self):
        return self._config_entry.data[CONF_USERNAME]

    @property
    def password(self):
        return self._config_entry.data[CONF_PASSWORD]

    @property
    def url(self):
        return self._config_entry.data[CONF_URL]

    @property
    def site(self):
        return self._config_entry.data[CONF_SITE]

    @property
    def verify_ssl(self):
        return self._config_entry.data[CONF_VERIFY_SSL]

    @property
    def ssid_filter(self):
        return self._config_entry.data[CONF_SSID_FILTER]

    @property
    def signal_update(self):
        return f"{OMADA_DOMAIN}-update-{self._config_entry.entry_id}"

    @property
    def signal_options_update(self):
        return f"{OMADA_DOMAIN}-options-{self._config_entry.entry_id}"

    async def async_setup(self):
            
        self.api = await get_api_controller(self.hass, self.url, self.username, self.password, self.site, self.verify_ssl)
        await self.update_devices()

        self.async_on_close(
            async_track_time_interval(self.hass, self.update_all, SCAN_INTERVAL)
        )

        self._config_entry.add_update_listener(self.async_config_entry_updated)

    async def update_all(self, now):
        await self.update_devices()

    async def update_devices(self):

        LOGGER.debug("Updating clients...")
        
        for _ in range(2):
            try:
                await self.api.devices.update()
                await self.api.clients.update()
                await self.api.known_clients.update()
                break
            except LoginRequired:
                LOGGER.warning("Token possibly expired to Omada API. Renewing...")
                self.api.login()
            except RequestError as err:
                LOGGER.error("Unable to connect to Omada: %s", err)
            except OmadaApiException as err:
                LOGGER.error("Omada API error: %s", err)

        async_dispatcher_send(self.hass, self.signal_update)

    @callback
    def async_on_close(self, func: CALLBACK_TYPE) -> None:
        """Add a function to call when router is closed."""
        self._on_close.append(func)

    async def async_close(self):
        
        for func in self._on_close:
            func()

        return await self.hass.config_entries.async_unload_platforms(self._config_entry, [DOMAIN])

    @staticmethod
    async def async_config_entry_updated(hass, config_entry):
        if not (controller := hass.data[OMADA_DOMAIN].get(config_entry.entry_id)[DATA_OMADA]):
            return

        controller.load_config_entry_options()
        async_dispatcher_send(hass, controller.signal_options_update)

async def get_api_controller(hass, url, username, password, site, verify_ssl):

    ssl_context = None

    if verify_ssl:
        session = aiohttp_client.async_get_clientsession(hass)
        if isinstance(verify_ssl, str):
            ssl_context = ssl.create_default_context(cafile=verify_ssl)
    else:
        session = aiohttp_client.async_create_clientsession(
            hass, verify_ssl=verify_ssl, cookie_jar=CookieJar(unsafe=True)
        )

    controller = Controller(url, username, password, session, site=site, ssl_context=ssl_context)

    try:
        with async_timeout.timeout(10):
            await controller.login()
        
        with async_timeout.timeout(10):
            await controller.update_status()

        with async_timeout.timeout(10):
            await controller.update_ssids()

        return controller
    except LoginFailed as err:
        LOGGER.warning("Connected to Omada at %s but unauthorized: %s", url, err)
        raise AuthenticationRequired
    except RequestError as err:
        LOGGER.warning("Unable to connect to Omada at %s: %s", url, err)
        raise CannotConnect
