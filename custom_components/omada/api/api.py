import logging
import json

from .errors import(OmadaApiException)

LOGGER = logging.getLogger(__name__)

class APIItems:

    def __init__(self, request, end_point, key, item_cls):
        self._request = request
        self._end_point = end_point
        self.items = {}
        self._key = key
        self._item_cls = item_cls

    async def update(self):
        response = await self._request("GET", self._end_point, params=[("filters.active", "true"), ("currentPage", "1"), ("currentPageSize", "1000000")])

        if "data" in response:
            self._process_raw(response["data"])
        else:
            raise OmadaApiException(f"Unable to parse {{self._end_point}}: 'data' array not available in response.")

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
            if not key in present_items:
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

class APIItem:

    def __init__(self, raw):
        self._raw = raw

    def update(self, raw=None):
        if raw:
            self._raw = raw
        else:
            return