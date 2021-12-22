from homeassistant.components.device_tracker.const import DOMAIN
from homeassistant.helpers.config_validation import multi_select
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from homeassistant.const import (
    CONF_URL, CONF_USERNAME, CONF_PASSWORD, CONF_VERIFY_SSL
)

import homeassistant.helpers.config_validation as cv

from .api.errors import LoginFailed, LoginRequired, OmadaApiException, RequestError, SSLError, InvalidURLError, UnknownSite, UnsupportedVersion

from .const import (DATA_OMADA, DOMAIN as OMADA_DOMAIN, CONF_SITE, CONF_SSID_FILTER)
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
        self.controller: OmadaController = self.hass.data[OMADA_DOMAIN][self.config_entry.entry_id][DATA_OMADA]

        return await self.async_step_device_tracker()

    async def async_step_device_tracker(self, user_input=None):
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        ssid_filter = {ssid: ssid for ssid in sorted(self.controller.api.ssids)}

        return self.async_show_form(
            step_id="device_tracker",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SSID_FILTER, default=self.controller.option_ssid_filter
                    ): cv.multi_select(ssid_filter)
                }
            ),
            last_step=True
        )

    async def _update_options(self):
        return self.async_create_entry(title="", data=self.options)
