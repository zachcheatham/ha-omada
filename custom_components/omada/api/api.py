import logging

from typing import Any, Callable, Dict
from abc import abstractmethod

from .errors import (OmadaApiException)

LOGGER = logging.getLogger(__name__)

class APIItem:
    def __init__(self, raw):
        self._raw: Dict[str, Any] = raw
        self._details: Dict[str, Any] = {}

    def update(self, raw=None):
        if raw:
            self._raw = raw
        else:
            return


class APIItems:

    _has_details = False

    def __init__(self, request: Callable[[str, str, list[Dict[str, str]]], Any], end_point: str, key: str,
                 item_cls: str, data_key: str = ""):
        self._request: Callable[[
            str, str, list[Dict[str, str]]], Any] = request
        self._end_point: str = end_point
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

        if update_details and self._has_details:
            for key, item in self.items.items():
                await self.update_details(key, item)         

    @abstractmethod
    def update_details(self, key: str, item: APIItem) -> None:
        pass

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

    def __getitem__(self, obj_id):
        try:
            return self.items[obj_id]
        except KeyError:
            LOGGER.error(f"Couldn't find key: {obj_id}")

    def __iter__(self):
        return self.items.__iter__()
