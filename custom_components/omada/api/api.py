import logging

from typing import Any, Callable, Dict

from .errors import (OmadaApiException)

LOGGER = logging.getLogger(__name__)


class APIItems:
    def __init__(self, request: Callable[[str, str, list[Dict[str, str]]], Any], end_point: str, key: str,
                 item_cls: str, data_key: str = "", details_end_point: str | None = None, details_properties: list[str] | None = None):
        self._request: Callable[[
            str, str, list[Dict[str, str]]], Any] = request
        self._end_point: str = end_point
        self._details_end_point: str | None = details_end_point
        self._details_properties: list[str] | None = details_properties
        self.items: Dict[str, Any] = {}
        self._key: str = key
        self._item_cls = item_cls
        self._data_key: str = data_key

    async def update(self, update_details: bool = False):
        response = await self._request("GET", self._end_point, params=[
            ("filters.active", "true"), ("currentPage",
                                         "1"), ("currentPageSize", "1000000")
        ])

        if self._data_key == "":
            # Response is a list
            self._process_raw(response)
        elif self._data_key in response:
            # Response is a dict, process a specific key containing a list
            self._process_raw(response[self._data_key])
        else:
            raise OmadaApiException(
                f"Unable to parse {{self._end_point}}: '{self._data_key}' array not available in response.")

        if update_details and self._details_end_point is not None:
            for key in self.items:
                response = await self._request("GET", self._details_end_point.replace('%key', key))
                self._process_raw_detail(response, key)

    def _process_raw(self, raw):
        present_items = set()
        removed_items = set()

        for raw_item in raw:
            key = raw_item[self._key]
            present_items.add(key)
            existing = self.items.get(key)

            if existing is not None:
                existing.update(raw=raw_item)
            else:
                self.items[key] = self._item_cls(raw_item)

        for key in self.items:
            if key not in present_items:
                removed_items.add(key)

        for key in removed_items:
            self.items.pop(key)

    def _process_raw_detail(self, raw: dict, key: str):
        if key not in self.items:
            LOGGER.warning(
                "Asked to process details for %s key %s but does not exist in items.")
        else:
            details: dict = None

            if self._details_properties is not None:
                details = {}
                for property in self._details_properties:
                    details[property] = raw[property]
            else:
                details = raw

            self.items[key]._details = details

    def __getitem__(self, obj_id):
        try:
            return self.items[obj_id]
        except KeyError:
            LOGGER.error(f"Couldn't find key: {obj_id}")

    def __iter__(self):
        return self.items.__iter__()


class APIItem:
    def __init__(self, raw):
        self._raw: Dict[str, Any] = raw
        self._details: Dict[str, Any] = {}

    def update(self, raw=None):
        if raw:
            self._raw = raw
        else:
            return
