from platform import version
from aiohttp.client import ClientSession
from custom_components.omada.api.clients import Clients
from custom_components.omada.api.devices import Devices
import logging

from aiohttp import client_exceptions

from .clients import Clients
from .devices import Devices
from .known_clients import KnownClients
from .errors import (
    HttpErrorCode,
    InvalidURLError,
    SSLError,
    UnknownSite,
    raise_response_error,
    UnsupportedVersion,
    RequestError,
)

LOGGER = logging.getLogger(__name__)

API_PATH = "/api/v2"
class Controller:
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        websession: ClientSession,
        site: str = "Default",
        ssl_context=None,
    ):

        self.url = url
        self.site = site
        self.role_type = 0
        self.name = None
        self.version = None
        self._username = username
        self._password = password
        self._session = websession
        self._ssl_context = ssl_context
        self._controller_id = None
        self._site_id = None
        self._token = None
        self.clients = Clients(self._site_request)
        self.devices = Devices(self._site_request)
        self.known_clients = KnownClients(self._site_request)
        self.ssids = set()

    async def login(self) -> None:
        """Call to obtain login token, controller id, and site id."""

        # Update API information before doing anything. This also ensures we correctly recover from controller upgrades.
        await self._update_api_info()

        auth = {"username": self._username, "password": self._password}
        response = await self._controller_request("post", "/login", json=auth)

        self.role_type = response["roleType"]
        self._token = response["token"]

        LOGGER.info(f"Login successful. Role type {self.role_type}.")

        if (
            self.version >= "5.0.0"
        ):  # Aquire site id for site name as required for versions 5+
            await self._update_site_id()

    async def _update_api_info(self):
        """Obtain basic API information required to properly interact with different versions of the API."""

        response = await self._request("get", f"{self.url}/api/info")
        self.version = response["controllerVer"]
        if self.version >= "5.0.0":
            self._controller_id = response["omadacId"]

    async def _update_site_id(self):
        """Obtain site id for specified site name. Required in v5.0.0+"""

        response = await self._controller_request(
            "get",
            "/users/current",
            params=[("currentPage", "1"), ("currentPageSize", "10000")],
            private=True,
        )

        LOGGER.debug("current user %s", response)
        for site in response["privilege"]["sites"]:
            if site["name"] == self.site:
                self._site_id = site["key"]
                break

        if not self._site_id:
            raise UnknownSite(f"Unknown site '{self.site}'")

    async def update_status(self):
        """Update controller name."""

        response = await self._controller_request(
            "get", "/maintenance/controllerStatus", private=True
        )
        self.name = response["name"]

    async def update_ssids(self):
        """Retrieve the list of avaiable SSIDs within a site."""

        if self.version < "4.4.8":
            response = await self._site_request("get", "/setting/ssids")

            self.ssids.clear()

            for ssid in response["ssids"][0]["ssidList"]:
                self.ssids.add(ssid["ssidName"])

        else:
            response = await self._site_request("get", "/setting/wlans")

            self.ssids.clear()

            # The key of the id changed in v5
            wland_id_key=None
            if self.version >= "5.0.0":
                wland_id_key = "id"
            else:
                wland_id_key = "wlanId"

            for wlan in response["data"]:
                wlan_id = wlan[wland_id_key]
                ssid_response = await self._site_request(
                    "get", f"/setting/wlans/{wlan_id}/ssids"
                )

                for ssid in ssid_response["data"]:
                    self.ssids.add(ssid["name"])

    async def _site_request(self, method, end_point, params=None, json=None):
        """Perform a request specific to a site."""

        endpoint = None
        if self.version >= "5.0.0":
            endpoint = f"/sites/{self._site_id}{end_point}"
        else:
            endpoint = f"/sites/{self.site}{end_point}"

        return await self._controller_request(method, endpoint, params=params, json=json, private=True)

    async def _controller_request(
        self, method, end_point, params=None, json=None, private=False
    ):
        """Perform a request specific to the controlller"""

        if not self.version:
            raise Exception(
                "Controller version has not been fetched. Please call update_status() first."
            )

        url = None
        if self.version >= "5.0.0":
            url = f"{self.url}/{self._controller_id}{API_PATH}{end_point}"
        else:
            url = f"{self.url}{API_PATH}{end_point}"

        return await self._request(
            method, url, params=params, json=json, private=private
        )

    async def _request(self, method, url, params=None, json=None, private=False):
        """Perform a request. Will automatically handle the login token if private is set to True."""

        headers = {}

        if private:
            if not self.version:
                raise Exception(
                    "Controller version has not been fetched. Please call update_status() first."
                )

            if self.version >= "5.0.0":
                headers["Csrf-Token"] = self._token
            else:
                if params is None:
                    params = []
                params.append(("token", self._token))

        LOGGER.debug("Requesting: %s - Params: %s - JSON: %s - Headers %s", url, params, json, headers)

        try:
            async with self._session.request(
                method,
                url,
                params=params,
                headers=headers,
                json=json,
                ssl=self._ssl_context,
            ) as res:
                LOGGER.debug("%s %s %s", res.status, res.content_type, res)

                if res.status != 200:
                    if res.content_type == "application/json":
                        response = await res.json()
                        self._raiseOnResponseError(url, response)

                    LOGGER.warning(
                        f"Error connecting to {url}: API returned HTTP {res.status}."
                    )
                    raise HttpErrorCode(url=url, code=res.status)

                if res.content_type == "application/json":
                    response = await res.json()
                    self._raiseOnResponseError(url, response)
                    if "result" in response:
                        return response["result"]
                    return response
                else:
                    raise RequestError("Received non-json response!")

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
