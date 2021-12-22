from custom_components.omada.api.clients import Clients
from custom_components.omada.api.devices import Devices
import logging

from aiohttp import client_exceptions

from .clients import Clients
from .devices import Devices
from .known_clients import KnownClients
from .errors import (HttpErrorCode, InvalidURLError, SSLError, raise_response_error, OmadaApiException, RequestError)

LOGGER = logging.getLogger(__name__)

API_PATH = "/api/v2"

class Controller:

    def __init__(self, url, username, password, websession, site="Default", ssl_context=None):

        self.url = url
        self.site = site
        self.role_type = 0
        self.name = None
        self.version = None
        self._username = username
        self._password = password
        self._session = websession
        self._ssl_context = ssl_context
        self._token = None
        self.clients = Clients(self._site_request)
        self.devices = Devices(self._site_request)
        self.known_clients = KnownClients(self._site_request)
        self.ssids = set()

    async def login(self):
        auth = {
            "username": self._username,
            "password": self._password
        }

        response = await self._public_request("post", "/login", json=auth)
        self.role_type = response["roleType"]
        self._token = response["token"]
        LOGGER.info(f"Login successful. Role type {self.role_type}.")

    async def update_status(self):
        response = await self._private_request("get", "/maintenance/controllerStatus")
        self.name = response["name"]
        self.version = response["controllerVersion"]

    async def update_ssids(self):
        response = await self._site_request("get", "/setting/ssids")
        self.ssids.clear()
        for ssid in response["ssids"][0]["ssidList"]:
            self.ssids.add(ssid["ssidName"])

    async def _site_request(self, method, end_point, params=[], json=None):
        url = f"{self.url}{API_PATH}/sites/{self.site}{end_point}"

        tokened_params=[("token", self._token)] + params

        return await self._request(method, url, params=tokened_params, json=json)

    async def _private_request(self, method, end_point, params=[], json=None):
        url = f"{self.url}{API_PATH}{end_point}"

        tokened_params=[("token", self._token)] + params

        return await self._request(method, url, params=tokened_params, json=json)

    async def _public_request(self, method, end_point, json=None):
        url = f"{self.url}{API_PATH}{end_point}"
        return await self._request(method, url, json=json)

    async def _request(self, method, url, params=None, json=None):
        LOGGER.debug("Requesting: %s - Params: %s - JSON: %s", url, params, json)

        try:
            async with self._session.request(method, url, params=params, json=json, ssl=self._ssl_context) as res:
                LOGGER.debug("%s %s %s", res.status, res.content_type, res)

                if res.status != 200:
                    if res.content_type == "application/json":
                        response = await res.json()
                        self._raiseOnResponseError(url, response)
                    
                    LOGGER.warning(f"Error connecting to {url}: API returned HTTP {res.status}.")
                    raise HttpErrorCode(url=url, code=res.status)

                if res.content_type == "application/json":
                    response = await res.json()
                    self._raiseOnResponseError(url, response)
                    if "result" in response:
                        return response["result"]
                    return response
            
                return res

        except client_exceptions.ClientConnectorCertificateError as err:
            raise SSLError(f"Error connecting to {url}: {err}")
        except client_exceptions.InvalidURL as err:
            raise InvalidURLError
        except client_exceptions.ClientError as err:
            raise RequestError(f"Error connecting to {url}: {err}") from None


    def _raiseOnResponseError(self, url, response):
        if not isinstance(response, dict):
            return

        if "errorCode" in response and response["errorCode"] != 0:
            raise_response_error(url, response)

