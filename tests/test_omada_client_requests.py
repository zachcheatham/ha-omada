import importlib.util
import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "custom_components" / "omada" / "api"


def _ensure_package(name: str) -> None:
    if name in sys.modules:
        return

    module = types.ModuleType(name)
    module.__path__ = []
    sys.modules[name] = module


def _load_module(module_name: str, file_name: str):
    spec = importlib.util.spec_from_file_location(module_name, API_ROOT / file_name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_omada_api_modules():
    _ensure_package("test_omada")
    _ensure_package("test_omada.api")

    errors = _load_module("test_omada.api.errors", "errors.py")
    api = _load_module("test_omada.api.api", "api.py")
    clients = _load_module("test_omada.api.clients", "clients.py")
    return errors, api, clients


def load_omada_controller_module():
    _ensure_package("test_omada")
    _ensure_package("test_omada.api")

    if "aiohttp" not in sys.modules:
        aiohttp = types.ModuleType("aiohttp")
        aiohttp.client_exceptions = types.SimpleNamespace(
            ClientConnectorCertificateError=type("ClientConnectorCertificateError", (Exception,), {}),
            InvalidURL=type("InvalidURL", (Exception,), {}),
            ClientError=type("ClientError", (Exception,), {}),
        )
        sys.modules["aiohttp"] = aiohttp

    if "aiohttp.client" not in sys.modules:
        aiohttp_client = types.ModuleType("aiohttp.client")
        aiohttp_client.ClientSession = object
        sys.modules["aiohttp.client"] = aiohttp_client

    _load_module("test_omada.api.errors", "errors.py")
    _load_module("test_omada.api.api", "api.py")
    _load_module("test_omada.api.clients", "clients.py")
    _load_module("test_omada.api.devices", "devices.py")
    _load_module("test_omada.api.known_clients", "known_clients.py")
    return _load_module("test_omada.api.controller", "controller.py")


class ClientsRequestTests(unittest.IsolatedAsyncioTestCase):
    async def test_legacy_client_update_uses_get_with_query_filters(self):
        _, _, clients_module = load_omada_api_modules()
        captured = {}

        async def request(method, end_point, params=None, json=None):
            captured["method"] = method
            captured["end_point"] = end_point
            captured["params"] = params
            captured["json"] = json
            return {"data": []}

        clients = clients_module.Clients(request)

        await clients.update()

        self.assertEqual(captured["method"], "GET")
        self.assertEqual(captured["end_point"], "/clients")
        self.assertEqual(
            captured["params"],
            [("filters.active", "true"), ("currentPage", "1"), ("currentPageSize", "1000000")],
        )
        self.assertIsNone(captured["json"])

    async def test_v6_client_update_uses_openapi_post_payload(self):
        _, _, clients_module = load_omada_api_modules()
        captured = {}

        async def request(method, end_point, params=None, json=None):
            captured["method"] = method
            captured["end_point"] = end_point
            captured["params"] = params
            captured["json"] = json
            return {"data": []}

        clients = clients_module.Clients(request)
        clients.use_v6_openapi = True

        await clients.update()

        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["end_point"], "/clients")
        self.assertIsNone(captured["params"])
        self.assertEqual(
            captured["json"],
            {
                "filters": {"active": True},
                "sorts": {},
                "hideHealthUnsupported": True,
                "page": 1,
                "pageSize": 100,
                "scope": 1,
            },
        )

    async def test_v6_controller_client_update_uses_openapi_site_url(self):
        controller_module = load_omada_controller_module()

        controller = controller_module.Controller(
            url="https://controller.example.com",
            username="user",
            password="pass",
            req_timeout=30,
            websession=None,
        )
        controller.version = "6.2.0.17"
        controller.controller_id = "controller-id"
        controller._site_id = "site-id"
        controller._token = "csrf-token"
        controller.clients.use_v6_openapi = True

        captured = {}

        async def fake_request(method, url, params=None, json=None, private=False, extra_headers=None):
            captured["method"] = method
            captured["url"] = url
            captured["params"] = params
            captured["json"] = json
            captured["private"] = private
            captured["extra_headers"] = extra_headers
            return {"data": []}

        controller._request = fake_request

        await controller.clients.update()

        self.assertEqual(captured["method"], "POST")
        self.assertEqual(
            captured["url"],
            "https://controller.example.com/openapi/v2/controller-id/sites/site-id/clients",
        )
        self.assertTrue(captured["private"])
        self.assertEqual(
            captured["extra_headers"],
            {
                "X-Requested-With": "XMLHttpRequest",
                "Omada-Request-Source": "web-local",
            },
        )


if __name__ == "__main__":
    unittest.main()