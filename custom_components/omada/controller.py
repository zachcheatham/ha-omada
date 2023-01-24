import logging
import ssl
from datetime import timedelta

from aiohttp import CookieJar
from homeassistant.components.device_tracker import DOMAIN
from homeassistant.const import (CONF_PASSWORD, CONF_URL, CONF_USERNAME, CONF_VERIFY_SSL)
from homeassistant.core import CALLBACK_TYPE, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval

from .api.controller import Controller
from .api.errors import (LoginFailed, OmadaApiException, OperationForbidden, RequestError, LoginRequired, UnknownSite)
from .const import (CONF_SITE, CONF_SSID_FILTER, CONF_DISCONNECT_TIMEOUT, CONF_TRACK_CLIENTS,
                    CONF_TRACK_DEVICES, CONF_ENABLE_CLIENT_BANDWIDTH_SENSORS,
                    CONF_ENABLE_CLIENT_UPTIME_SENSORS, CONF_ENABLE_CLIENT_BLOCK_SWITCH,
                    CONF_ENABLE_DEVICE_BANDWIDTH_SENSORS, CONF_ENABLE_DEVICE_RADIO_UTILIZATION_SENSORS,
                    CONF_ENABLE_DEVICE_CONTROLS, CONF_ENABLE_DEVICE_STATISTICS_SENSORS,
                    CONF_ENABLE_DEVICE_CLIENTS_SENSORS, DOMAIN as OMADA_DOMAIN)

SCAN_INTERVAL = timedelta(seconds=30)  # TODO Remove after websockets

LOGGER = logging.getLogger(__name__)


class OmadaController:
    def __init__(self, hass, config_entry):
        self.hass = hass
        self._config_entry = config_entry
        self.api: Controller = None
        self.entities = {}
        self._on_close = []
        self.option_track_clients = True
        self.option_track_devices = True
        self.option_ssid_filter = None
        self.option_disconnect_timeout = 0
        self.option_client_bandwidth_sensors = False
        self.option_client_uptime_sensor = False
        self.option_client_block_switch = False
        self.option_device_bandwidth_sensors = False
        self.option_device_statistics_sensors = False
        self.option_device_clients_sensors = False
        self.option_device_radio_utilization_sensors = False
        self.option_device_controls = False
        self.available = True

        self.load_config_entry_options()

    def load_config_entry_options(self):
        options = self._config_entry.options

        self.option_ssid_filter = set(options.get(CONF_SSID_FILTER, []))
        self.option_disconnect_timeout = options.get(CONF_DISCONNECT_TIMEOUT, 0)
        self.option_track_clients = options.get(CONF_TRACK_CLIENTS, True)
        self.option_track_devices = options.get(CONF_TRACK_DEVICES, True)
        self.option_client_bandwidth_sensors = options.get(CONF_ENABLE_CLIENT_BANDWIDTH_SENSORS, False)
        self.option_client_uptime_sensor = options.get(CONF_ENABLE_CLIENT_UPTIME_SENSORS, False)
        self.option_client_block_switch = options.get(CONF_ENABLE_CLIENT_BLOCK_SWITCH, False)
        self.option_device_bandwidth_sensors = options.get(CONF_ENABLE_DEVICE_BANDWIDTH_SENSORS, False)
        self.option_device_statistics_sensors = options.get(CONF_ENABLE_DEVICE_STATISTICS_SENSORS, False)
        self.option_device_clients_sensors = options.get(CONF_ENABLE_DEVICE_CLIENTS_SENSORS, False)
        self.option_device_radio_utilization_sensors = options.get(CONF_ENABLE_DEVICE_RADIO_UTILIZATION_SENSORS, False)
        self.option_device_controls = options.get(CONF_ENABLE_DEVICE_CONTROLS, False)

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
    def disconnect_timeout(self):
        return self._config_entry.data[CONF_DISCONNECT_TIMEOUT]

    @property
    def signal_update(self):
        return f"{OMADA_DOMAIN}-update-{self._config_entry.entry_id}"

    @property
    def signal_options_update(self):
        return f"{OMADA_DOMAIN}-options-{self._config_entry.entry_id}"

    async def async_setup(self):
        try:
            self.api = await get_api_controller(
                self.hass, self.url, self.username, self.password, self.site, self.verify_ssl
            )
        except LoginFailed as err:
            raise ConfigEntryAuthFailed from err
        except OmadaApiException as err:
            raise ConfigEntryNotReady from err
        except TimeoutError as err:
            raise ConfigEntryNotReady from err

        await self.update_devices()

        self.async_on_close(async_track_time_interval(self.hass, self.update_all, SCAN_INTERVAL))

        self._config_entry.add_update_listener(self.async_config_entry_updated)

    async def update_all(self, now):
        await self.update_devices()

    async def update_devices(self):
        LOGGER.debug("Updating clients...")

        available = False

        for _ in range(2):
            try:
                if self.option_track_devices:
                    await self.api.devices.update()

                if self.option_track_clients:
                    await self.api.clients.update()
                    await self.api.known_clients.update()

                available = True

                break
            except LoginRequired:
                LOGGER.warning("Token possibly expired to Omada API. Renewing...")
                await self.api.login()
            except RequestError as err:
                LOGGER.error("Unable to connect to Omada: %s. Renewing login...", err)
                await self.api.login()
            except OmadaApiException as err:
                LOGGER.error("Omada API error: %s", err)

        self.available = available

        async_dispatcher_send(self.hass, self.signal_update)

    @callback
    def async_on_close(self, func: CALLBACK_TYPE) -> None:
        """Add a function to call when router is closed."""
        self._on_close.append(func)

    async def async_close(self):
        for func in self._on_close:
            func()

        return await self.hass.config_entries.async_unload_platforms(self._config_entry, [DOMAIN])

    def get_clients_filtered(self) -> list[str]:
        return [
            mac for mac in self.api.clients
            if not self.option_ssid_filter or self.api.clients[mac].ssid in self.option_ssid_filter
        ]

    @staticmethod
    async def async_config_entry_updated(hass, config_entry):
        if not (controller := hass.data[OMADA_DOMAIN].get(config_entry.entry_id)):
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
        await controller.login()

        await controller.update_status()

        try:
            await controller.update_ssids()
        except OperationForbidden as err:
            if controller.version < "5.0.0":
                LOGGER.warning("API returned 'operation forbidden' while retrieving SSID stats. This is "
                                "indicative of an invalid site id.")
                raise UnknownSite(f"Possible invalid site '{site}'.")
            else:
                raise err

        return controller
    except LoginFailed as err:
        LOGGER.warning("Connected to Omada at %s but unauthorized: %s", url, err)
        raise err
    except OmadaApiException as err:
        LOGGER.warning("Unable to connect to Omada at %s: %s", url, err)
        raise err
