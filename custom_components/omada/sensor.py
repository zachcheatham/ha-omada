from datetime import datetime, timedelta

from homeassistant.components.sensor import DOMAIN, DEVICE_CLASS_TIMESTAMP, SensorEntity
from homeassistant.const import UnitOfInformation, UnitOfDataRate
from homeassistant.core import callback
from homeassistant.helpers import entity_registry
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_registry import async_entries_for_config_entry
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.util import dt as dt_util

from .controller import OmadaController

from .const import (DOMAIN as OMADA_DOMAIN)
from .omada_client import OmadaClient

DOWNLOAD_SENSOR = "downloaded"
UPLOAD_SENSOR = "uploaded"
UPTIME_SENSOR = "uptime"
RX_SENSOR = "rx"
TX_SENSOR = "tx"

async def async_setup_entry(hass, config_entry, async_add_entities):
    controller: OmadaController = hass.data[OMADA_DOMAIN][config_entry.entry_id]
    controller.entities[DOMAIN] = {
        DOWNLOAD_SENSOR: set(),
        UPLOAD_SENSOR: set(),
        UPTIME_SENSOR: set(),
        RX_SENSOR: set(),
        TX_SENSOR: set()
    }


    er = entity_registry.async_get(hass)
    initial_client_set = controller.get_clients_filtered()

    # Add entries that used to exist in HA but are now disconnected.
    for entry in async_entries_for_config_entry(er, config_entry.entry_id):
        if entry.domain == DOMAIN:
            mac = entry.unique_id.split("-", 1)[1]

            if mac not in controller.api.devices:
                if mac not in controller.api.clients:
                    if mac in controller.api.known_clients:
                        initial_client_set.append(mac)
                elif controller.option_ssid_filter and controller.api.clients[mac].ssid not in controller.option_ssid_filter:
                    er.async_remove(entry.entity_id)

    @callback
    def items_added(clients: set = None) -> None:

        if (clients is None):
            clients = controller.get_clients_filtered()
        
        add_bandwidth_entities(clients, controller, async_add_entities)
        add_uptime_entities(clients, controller, async_add_entities)

        for signal in (controller.signal_update, controller.signal_options_update):
            config_entry.async_on_unload(async_dispatcher_connect(hass, signal, items_added))

    items_added(initial_client_set)

@callback
def add_bandwidth_entities(clients: set, controller: OmadaController, async_add_entities):

    sensors = []

    for mac in clients:
        for sensor_class in (OmadaDownloadBandwidthSensor, OmadaUploadBandwidthSensor, OmadaRXSensor, OmadaTXSensor):
            if mac not in controller.entities[DOMAIN][sensor_class.TYPE]:
                sensors.append(sensor_class(controller, mac))

    if sensors:
        async_add_entities(sensors)


@callback
def add_uptime_entities(clients: set, controller: OmadaController, async_add_entities):

    sensors = []

    for mac in clients:
        if mac not in controller.entities[DOMAIN][UPTIME_SENSOR]:
            sensors.append(OmadaUptimeSensor(controller, mac))

    if sensors:
        async_add_entities(sensors)


class OmadaBandwidthSensor(OmadaClient, SensorEntity):
     
    DOMAIN = DOMAIN

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfInformation.MEGABYTES

    @property
    def name(self) -> str:
        return f"{super().name} {self.TYPE.title()}"

class OmadaDownloadBandwidthSensor(OmadaBandwidthSensor):

    TYPE = DOWNLOAD_SENSOR

    @property
    def native_value(self) -> int:
        return self._controller.api.known_clients[self.key].download / 1000000

class OmadaUploadBandwidthSensor(OmadaBandwidthSensor):

    TYPE = UPLOAD_SENSOR

    @property
    def native_value(self) -> int:
        return self._controller.api.known_clients[self.key].upload / 1000000
    
class OmadaDataRateSensor(OmadaClient, SensorEntity):
    
    DOMAIN = DOMAIN

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfDataRate.MEGABYTES_PER_SECOND

    @property
    def name(self) -> str:
        return f"{super().name} {self.TYPE.upper()} Activity"
    
class OmadaRXSensor(OmadaDataRateSensor):

    TYPE = RX_SENSOR

    @property
    def native_value(self) -> int:
        if self.key in self._controller.api.clients:
            return self._controller.api.clients[self.key].rx_rate / 1000000
        else:
            return 0
    

class OmadaTXSensor(OmadaDataRateSensor):

    TYPE = TX_SENSOR

    @property
    def native_value(self) -> int:
        if self.key in self._controller.api.clients:
            return self._controller.api.clients[self.key].tx_rate / 1000000
        else:
            return 0
    

class OmadaUptimeSensor(OmadaClient, SensorEntity):

    DOMAIN = DOMAIN
    TYPE = UPTIME_SENSOR

    _attr_device_class = DEVICE_CLASS_TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, controller, mac):
        super().__init__(controller, mac)
        self.last_uptime = self.uptime

    @callback
    async def async_update(self) -> None:
        update_state = True

        if (self.last_uptime == self.uptime or
            (self.last_uptime >= 0 and self.uptime > self.last_uptime)
        ):
            update_state = False

        self.last_uptime = self.uptime

        if update_state:
            await super().async_update()
        
    @property
    def name(self) -> str:
        return f"{super().name} {self.TYPE.title()}"
    
    @property
    def native_value(self) -> datetime:
        if self.uptime == -1:
            return None
        
        return dt_util.now() - timedelta(seconds=self.uptime)
    
    @property
    def uptime(self) -> int:
        if self.key in self._controller.api.clients:
            return self._controller.api.clients[self.key].uptime
        else:
            return -1

