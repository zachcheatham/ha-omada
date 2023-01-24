from datetime import datetime, timedelta

from homeassistant.components.sensor import (DOMAIN, DEVICE_CLASS_TIMESTAMP,
                                             SensorEntity)
from homeassistant.const import UnitOfInformation, UnitOfDataRate, PERCENTAGE
from homeassistant.core import callback
from homeassistant.helpers import entity_registry
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_registry import async_entries_for_config_entry
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.util import dt as dt_util

from .controller import OmadaController

from .api.devices import Device
from .const import (DOMAIN as OMADA_DOMAIN)
from .omada_client import OmadaClient
from .omada_entity import OmadaEntity

DOWNLOAD_SENSOR = "downloaded"
UPLOAD_SENSOR = "uploaded"
UPTIME_SENSOR = "uptime"
RX_SENSOR = "rx"
TX_SENSOR = "tx"
CPU_USAGE_SENSOR = "cpu_usage"
MEMORY_USAGE_SENSOR = "memory_usage"
CLIENTS_SENSOR = "clients"
CLIENTS_2G_SENSOR = "2ghz_clients"
CLIENTS_5G_SENSOR = "5ghz_clients"
CLIENTS_6G_SENSOR = "6ghz_clients"


async def async_setup_entry(hass, config_entry, async_add_entities):
    controller: OmadaController = hass.data[OMADA_DOMAIN][config_entry.entry_id]
    controller.entities[DOMAIN] = {
        DOWNLOAD_SENSOR: set(),
        UPLOAD_SENSOR: set(),
        UPTIME_SENSOR: set(),
        RX_SENSOR: set(),
        TX_SENSOR: set(),
        CPU_USAGE_SENSOR: set(),
        MEMORY_USAGE_SENSOR: set(),
        CLIENTS_SENSOR: set(),
        CLIENTS_2G_SENSOR: set(),
        CLIENTS_5G_SENSOR: set(),
        CLIENTS_6G_SENSOR: set()
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
    def items_added(clients: set = None, devices: set = controller.api.devices) -> None:

        if (clients is None):
            clients = controller.get_clients_filtered()

        add_bandwidth_entities(clients, controller, async_add_entities)
        add_uptime_entities(clients, controller, async_add_entities)
        add_device_statistic_entities(devices, controller, async_add_entities)
        add_device_clients_entities(devices, controller, async_add_entities)

        for signal in (controller.signal_update, controller.signal_options_update):
            config_entry.async_on_unload(
                async_dispatcher_connect(hass, signal, items_added))

    items_added(initial_client_set)


@callback
def add_bandwidth_entities(clients: set, controller: OmadaController, async_add_entities):

    sensors = []

    for mac in clients:
        for sensor_class in (OmadaClientDownloadSensor, OmadaClientUploadSensor, OmadaClientRXSensor, OmadaClientTXSensor):
            if mac not in controller.entities[DOMAIN][sensor_class.TYPE]:
                sensors.append(sensor_class(controller, mac))

    if sensors:
        async_add_entities(sensors)


@callback
def add_uptime_entities(clients: set, controller: OmadaController, async_add_entities):

    sensors = []

    for mac in clients:
        if mac not in controller.entities[DOMAIN][UPTIME_SENSOR]:
            sensors.append(OmadaClientUptimeSensor(controller, mac))

    if sensors:
        async_add_entities(sensors)


@callback
def add_device_statistic_entities(devices: set, controller: OmadaController, async_add_entities):

    sensors = []

    for mac in devices:
        for sensor_class in (OmadaDeviceDownloadSensor,
                             OmadaDeviceUploadSensor,
                             OmadaDeviceRXSensor,
                             OmadaDeviceTXSensor,
                             OmadaDeviceUptimeSensor,
                             OmadaDeviceCPUUtilSensor,
                             OmadaDeviceMemUtilSensor,
                             ):
            if mac not in controller.entities[DOMAIN][sensor_class.TYPE]:
                sensors.append(sensor_class(controller, mac))

    if sensors:
        async_add_entities(sensors)


@callback
def add_device_clients_entities(devices: set, controller: OmadaController, async_add_entities):

    sensors = []

    for mac in devices:
        device: Device = controller.api.devices[mac]
        if not mac in controller.entities[DOMAIN][CLIENTS_2G_SENSOR]:
            sensors.append(OmadaDeviceClientsSensor(
                controller, mac, CLIENTS_2G_SENSOR))

        if not mac in controller.entities[DOMAIN][CLIENTS_SENSOR]:
            sensors.append(OmadaDeviceClientsSensor(
                controller, mac, CLIENTS_SENSOR))

        if device.supports_5ghz:
            if not mac in controller.entities[DOMAIN][CLIENTS_5G_SENSOR]:
                sensors.append(OmadaDeviceClientsSensor(
                    controller, mac, CLIENTS_5G_SENSOR))

        if device.supports_6ghz:
            if not mac in controller.entities[DOMAIN][CLIENTS_6G_SENSOR]:
                sensors.append(OmadaDeviceClientsSensor(
                    controller, mac, CLIENTS_6G_SENSOR))

    if sensors:
        async_add_entities(sensors)



class OmadaDeviceBandwidthSensor(OmadaEntity, SensorEntity):

    DOMAIN = DOMAIN

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfInformation.MEGABYTES

    @property
    def name(self) -> str:
        return f"{super().name} {self.TYPE.title()}"


class OmadaDeviceDownloadSensor(OmadaDeviceBandwidthSensor):

    TYPE = DOWNLOAD_SENSOR

    @property
    def native_value(self) -> int:
        return self._controller.api.devices[self.key].download / 1000000


class OmadaDeviceUploadSensor(OmadaDeviceBandwidthSensor):

    TYPE = UPLOAD_SENSOR

    @property
    def native_value(self) -> int:
        return self._controller.api.devices[self.key].upload / 1000000


class OmadaClientBandwidthSensor(OmadaClient, SensorEntity):

    DOMAIN = DOMAIN

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfInformation.MEGABYTES

    @property
    def name(self) -> str:
        return f"{super().name} {self.TYPE.title()}"


class OmadaClientDownloadSensor(OmadaClientBandwidthSensor):

    TYPE = DOWNLOAD_SENSOR

    @property
    def native_value(self) -> int:
        return self._controller.api.known_clients[self.key].download / 1000000


class OmadaClientUploadSensor(OmadaClientBandwidthSensor):

    TYPE = UPLOAD_SENSOR

    @property
    def native_value(self) -> int:
        return self._controller.api.known_clients[self.key].upload / 1000000


class OmadaDeviceDataRateSensor(OmadaEntity, SensorEntity):

    DOMAIN = DOMAIN

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfDataRate.MEGABYTES_PER_SECOND

    @property
    def name(self) -> str:
        return f"{super().name} {self.TYPE.upper()} Activity"


class OmadaDeviceRXSensor(OmadaDeviceDataRateSensor):

    TYPE = RX_SENSOR

    @property
    def native_value(self) -> int:
        return self._controller.api.devices[self.key].rx_rate / 1000000


class OmadaDeviceTXSensor(OmadaDeviceDataRateSensor):

    TYPE = TX_SENSOR

    @property
    def native_value(self) -> int:
        return self._controller.api.devices[self.key].tx_rate / 1000000


class OmadaClientDataRateSensor(OmadaClient, SensorEntity):

    DOMAIN = DOMAIN

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfDataRate.MEGABYTES_PER_SECOND

    @property
    def name(self) -> str:
        return f"{super().name} {self.TYPE.upper()} Activity"


class OmadaClientRXSensor(OmadaClientDataRateSensor):

    TYPE = RX_SENSOR

    @property
    def native_value(self) -> int:
        if self.key in self._controller.api.clients:
            return self._controller.api.clients[self.key].rx_rate / 1000000
        else:
            return 0


class OmadaClientTXSensor(OmadaClientDataRateSensor):

    TYPE = TX_SENSOR

    @property
    def native_value(self) -> int:
        if self.key in self._controller.api.clients:
            return self._controller.api.clients[self.key].tx_rate / 1000000
        else:
            return 0


class OmadaClientUptimeSensor(OmadaClient, SensorEntity):

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


class OmadaDeviceUptimeSensor(OmadaEntity, SensorEntity):

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
            self.uptime > self.last_uptime
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
        return dt_util.now() - timedelta(seconds=self.uptime)

    @property
    def uptime(self) -> int:
        return self._controller.api.devices[self.key].uptime


class OmadaDeviceSensor(OmadaEntity, SensorEntity):

    DOMAIN = DOMAIN
    PROPERTY = ""

    def __init__(self, controller, mac):
        super().__init__(controller, mac)
        self.last_value = self.device_value

    @callback
    async def async_update(self) -> None:

        if (self.last_value != self.device_value):
            self.last_value = self.device_value
            await super().async_update()

    @property
    def name(self) -> str:
        return "{} {}".format(super().name, self.TYPE.replace("_", " ").title())
    
    @property
    def native_value(self):
        return self.last_value

    @property
    def device_value(self):
        return getattr(self._controller.api.devices[self.key], self.PROPERTY, None)


class OmadaDeviceCPUUtilSensor(OmadaDeviceSensor):

    TYPE = CPU_USAGE_SENSOR
    PROPERTY = "cpu"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = PERCENTAGE


class OmadaDeviceMemUtilSensor(OmadaDeviceSensor):

    TYPE = MEMORY_USAGE_SENSOR
    PROPERTY = "memory"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = PERCENTAGE


class OmadaDeviceClientsSensor(OmadaDeviceSensor):

    def __init__(self, controller, mac, type):
        self.TYPE = type

        if type == CLIENTS_SENSOR:
            self.PROPERTY = "clients"
        elif type == CLIENTS_2G_SENSOR:
            self.PROPERTY = "clients_2ghz"
        elif type == CLIENTS_5G_SENSOR:
            self.PROPERTY = "clients_5ghz"
        elif type == CLIENTS_6G_SENSOR:
            self.PROPERTY = "clients_6ghz"

        super().__init__(controller, mac)

    _attr_entity_category = EntityCategory.DIAGNOSTIC
