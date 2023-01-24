import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (CONF_URL, CONF_USERNAME, CONF_PASSWORD, CONF_VERIFY_SSL)
from homeassistant.core import callback

from .api.errors import LoginFailed, LoginRequired, OmadaApiException, RequestError, SSLError, InvalidURLError, \
    UnknownSite, UnsupportedVersion
from .const import (DOMAIN as OMADA_DOMAIN, CONF_SITE, CONF_SSID_FILTER, CONF_DISCONNECT_TIMEOUT,
                    CONF_TRACK_CLIENTS, CONF_TRACK_DEVICES, CONF_ENABLE_CLIENT_BANDWIDTH_SENSORS,
                    CONF_ENABLE_CLIENT_UPTIME_SENSORS, CONF_ENABLE_CLIENT_BLOCK_SWITCH,
                    CONF_ENABLE_DEVICE_BANDWIDTH_SENSORS, CONF_ENABLE_DEVICE_RADIO_UTILIZATION_SENSORS,
                    CONF_ENABLE_DEVICE_CONTROLS, CONF_ENABLE_DEVICE_STATISTICS_SENSORS,
                    CONF_ENABLE_DEVICE_CLIENTS_SENSORS)
from .controller import OmadaController, get_api_controller


class OmadaFlowHandler(config_entries.ConfigFlow, domain=OMADA_DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OmadaOptionsFlowHandler(config_entry)

    def __init__(self):
        self.config = {}

    @callback
    def _show_setup_form(self, user_input=None, errors=None):
        if user_input is None:
            user_input = {}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL, default=user_input.get(CONF_URL, "")): str,
                    vol.Optional(CONF_SITE, default=user_input.get(CONF_SITE, "Default")): str,
                    vol.Required(CONF_USERNAME, default=user_input.get(CONF_USERNAME, "")): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_VERIFY_SSL, default=user_input.get(CONF_VERIFY_SSL, True)): bool
                }
            ),
            errors=errors or {}
        )

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:

            user_input[CONF_URL] = user_input[CONF_URL].strip("/")

            self.config = {
                CONF_URL: user_input[CONF_URL],
                CONF_SITE: user_input[CONF_SITE],
                CONF_USERNAME: user_input[CONF_USERNAME],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_VERIFY_SSL: user_input[CONF_VERIFY_SSL]
            }

            try:
                controller = await get_api_controller(
                    self.hass,
                    self.config[CONF_URL],
                    self.config[CONF_USERNAME],
                    self.config[CONF_PASSWORD],
                    self.config[CONF_SITE],
                    self.config[CONF_VERIFY_SSL]
                )

                return self.async_create_entry(title=f"{controller.name}: {controller.site}", data=user_input)

            except (LoginFailed, LoginRequired):
                errors["base"] = "faulty_credentials"
            except InvalidURLError:
                errors["base"] = "invalid_url"
            except SSLError:
                errors["base"] = "ssl_error"
            except UnknownSite:
                errors["base"] = "unknown_site"
            except UnsupportedVersion:
                errors["base"] = "unsupported_version"
            except RequestError:
                errors["base"] = "service_unavailable"
            except OmadaApiException:
                errors["base"] = "api_error"

            return self._show_setup_form(user_input, errors)

        else:
            return self._show_setup_form(user_input, errors)


class OmadaOptionsFlowHandler(config_entries.OptionsFlow):

    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.options = dict(config_entry.options)
        self.controller = None

    async def async_step_init(self, user_input=None):
        self.controller: OmadaController = self.hass.data[OMADA_DOMAIN][self.config_entry.entry_id]

        return await self.async_step_device_tracker()

    async def async_step_device_tracker(self, user_input=None):
        if user_input is not None:
            self.options.update(user_input)
            if self.options[CONF_TRACK_CLIENTS]:
                return await self.async_step_client_options()
            elif self.options[CONF_TRACK_DEVICES]:
                return await self.async_step_device_options()
            else:
                return await self.async_step_controller_options()
        

        return self.async_show_form(
            step_id="device_tracker",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_TRACK_CLIENTS, default=self.controller.option_track_clients
                    ): bool,
                    vol.Optional(
                        CONF_TRACK_DEVICES, default=self.controller.option_track_devices
                    ): bool
                }
            ),
            last_step=False
        )
    
    async def async_step_client_options(self, user_input=None):
        if user_input is not None:
            self.options.update(user_input)
            if self.options[CONF_TRACK_DEVICES]:
                return await self.async_step_device_options()
            else:
                return await self.async_step_controller_options()
            
        ssid_filter = {ssid: ssid for ssid in sorted(self.controller.api.ssids)}

        return self.async_show_form(
            step_id="client_options",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SSID_FILTER, default=self.controller.option_ssid_filter
                    ): cv.multi_select(ssid_filter),
                    vol.Optional(
                        CONF_DISCONNECT_TIMEOUT, default=self.controller.option_disconnect_timeout
                    ): cv.positive_int,
                    vol.Optional(
                        CONF_ENABLE_CLIENT_BANDWIDTH_SENSORS,
                        default=self.controller.option_client_bandwidth_sensors
                    ): bool,
                    vol.Optional(
                        CONF_ENABLE_CLIENT_UPTIME_SENSORS,
                        default=self.controller.option_client_uptime_sensor
                    ): bool,
                    vol.Optional(
                        CONF_ENABLE_CLIENT_BLOCK_SWITCH,
                        default=self.controller.option_client_block_switch
                    ): bool
                }
            ),
            last_step=False
        )
    
    async def async_step_device_options(self, user_input=None):
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()
            #return await self.async_step_controller_options()
        
        return self.async_show_form(
            step_id="device_options",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_ENABLE_DEVICE_BANDWIDTH_SENSORS,
                        default=self.controller.option_device_bandwidth_sensors
                    ): bool,
                    vol.Optional(
                        CONF_ENABLE_DEVICE_STATISTICS_SENSORS,
                        default=self.controller.option_device_statistics_sensors
                    ): bool,
                    vol.Optional(
                        CONF_ENABLE_DEVICE_CLIENTS_SENSORS,
                        default=self.controller.option_device_clients_sensors
                    ): bool,
                    vol.Optional(
                        CONF_ENABLE_DEVICE_RADIO_UTILIZATION_SENSORS,
                        default=self.controller.option_device_radio_utilization_sensors
                    ): bool,
                    vol.Optional(
                        CONF_ENABLE_DEVICE_CONTROLS,
                        default=self.controller.option_device_controls
                    ): bool
                }
            ),
            last_step=True
        )

    async def _update_options(self):
        return self.async_create_entry(title="", data=self.options)
