import logging

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
from .omada_entity import OmadaClient, OmadaDevice

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
TX_UTILIZATION_2G_SENSOR = "2ghz_tx_utilization"
TX_UTILIZATION_5G_SENSOR = "5ghz_tx_utilization"
TX_UTILIZATION_6G_SENSOR = "6ghz_tx_utilization"
RX_UTILIZATION_2G_SENSOR = "2ghz_rx_utilization"
RX_UTILIZATION_5G_SENSOR = "5ghz_rx_utilization"
RX_UTILIZATION_6G_SENSOR = "6ghz_rx_utilization"
INTER_UTILIZATION_2G_SENSOR = "2ghz_interference_utilization"
INTER_UTILIZATION_5G_SENSOR = "5ghz_interference_utilization"
INTER_UTILIZATION_6G_SENSOR = "6ghz_interference_utilization"

LOGGER = logging.getLogger(__name__)

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
        CLIENTS_6G_SENSOR: set(),
        TX_UTILIZATION_2G_SENSOR: set(),
        TX_UTILIZATION_5G_SENSOR: set(),
        TX_UTILIZATION_6G_SENSOR: set(),
        RX_UTILIZATION_2G_SENSOR: set(),
        RX_UTILIZATION_5G_SENSOR: set(),
        RX_UTILIZATION_6G_SENSOR: set(),
        INTER_UTILIZATION_2G_SENSOR: set(),
        INTER_UTILIZATION_5G_SENSOR: set(),
        INTER_UTILIZATION_6G_SENSOR: set()
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
    def items_added(clients: set = None, devices: set = None) -> None:

        if controller.option_track_clients:
            if clients is None:
                clients = controller.get_clients_filtered()

            if controller.option_client_bandwidth_sensors:
                add_client_bandwidth_entities(clients, controller, async_add_entities)

            if controller.option_client_uptime_sensor:
                add_client_uptime_entities(clients, controller, async_add_entities)

        if controller.option_track_devices:

            if devices is None:
                devices = controller.api.devices

            if controller.option_device_statistics_sensors:
                add_device_statistic_entities(devices, controller, async_add_entities)

            if controller.option_device_bandwidth_sensors:
                add_device_bandwidth_entities(devices, controller, async_add_entities)

            if controller.option_device_clients_sensors:
                add_device_clients_entities(devices, controller, async_add_entities)

            if controller.option_device_radio_utilization_sensors:
                add_device_radio_entities(devices, controller, async_add_entities)

    for signal in (controller.signal_update, controller.signal_options_update):
        config_entry.async_on_unload(
            async_dispatcher_connect(hass, signal, items_added))

    items_added(initial_client_set)


@callback
def add_client_bandwidth_entities(clients: set, controller: OmadaController, async_add_entities):

    sensors = []

    for mac in clients:
        for sensor_class in (OmadaClientDownloadSensor, OmadaClientUploadSensor, OmadaClientRXSensor, OmadaClientTXSensor):
            if mac not in controller.entities[DOMAIN][sensor_class.TYPE]:
                sensors.append(sensor_class(controller, mac))

    if sensors:
        async_add_entities(sensors)


@callback
def add_client_uptime_entities(clients: set, controller: OmadaController, async_add_entities):

    sensors = []

    for mac in clients:
        if mac not in controller.entities[DOMAIN][UPTIME_SENSOR]:
            sensors.append(OmadaClientUptimeSensor(controller, mac))

    if sensors:
        async_add_entities(sensors)


class OmadaClientBandwidthSensor(OmadaClient, SensorEntity):

    DOMAIN = DOMAIN

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfInformation.MEGABYTES

    @property
    def name(self) -> str:
        return f"{super().name} {self.TYPE.title()}"
    
    @callback
    async def options_updated(self):
        if not self._controller.option_client_bandwidth_sensors:
            await self.remove()
        else:
            await super().options_updated()


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


class OmadaClientDataRateSensor(OmadaClient, SensorEntity):

    DOMAIN = DOMAIN

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfDataRate.MEGABYTES_PER_SECOND

    @property
    def name(self) -> str:
        return f"{super().name} {self.TYPE.upper()} Activity"
    
    @callback
    async def options_updated(self):
        if not self._controller.option_client_bandwidth_sensors:
            await self.remove()
        else:
            await super().options_updated()


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
        
    @callback
    async def options_updated(self):
        if not self._controller.option_client_uptime_sensor:
            await self.remove()
        else:
            await super().options_updated()

@callback
def add_device_bandwidth_entities(devices: set, controller: OmadaController, async_add_entities):
    sensors = []

    for mac in devices:
        for sensor_class in (OmadaDeviceDownloadSensor,
                             OmadaDeviceUploadSensor,
                             OmadaDeviceRXSensor,
                             OmadaDeviceTXSensor
                             ):
            if mac not in controller.entities[DOMAIN][sensor_class.TYPE]:
                sensors.append(sensor_class(controller, mac))

    if sensors:
        async_add_entities(sensors)

@callback
def add_device_statistic_entities(devices: set, controller: OmadaController, async_add_entities):

    sensors = []

    for mac in devices:
        for sensor_class in (OmadaDeviceUptimeSensor,
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


@callback
def add_device_radio_entities(devices: set, controller: OmadaController, async_add_entities):

    sensors = []

    for mac in devices:
        device: Device = controller.api.devices[mac]

        for sensor_type, property in ((TX_UTILIZATION_2G_SENSOR, "tx_utilization_2ghz"),
                                      (RX_UTILIZATION_2G_SENSOR, "rx_utilization_2ghz"),
                                      (INTER_UTILIZATION_2G_SENSOR, "interference_utilization_2ghz")
        ):

            if not mac in controller.entities[DOMAIN][sensor_type]:
                sensors.append(OmadaDeviceRadioUtilizationSensor(
                    controller, mac, sensor_type, property))

        if device.supports_5ghz:
            for sensor_type, property in ((TX_UTILIZATION_5G_SENSOR, "tx_utilization_5ghz"),
                                          (RX_UTILIZATION_5G_SENSOR, "rx_utilization_5ghz"),
                                          (INTER_UTILIZATION_5G_SENSOR, "interference_utilization_5ghz")
            ):

                if not mac in controller.entities[DOMAIN][sensor_type]:
                    sensors.append(OmadaDeviceRadioUtilizationSensor(
                        controller, mac, sensor_type, property))

        if device.supports_6ghz:
            for sensor_type, property in ((TX_UTILIZATION_6G_SENSOR, "tx_utilization_6ghz"),
                                          (RX_UTILIZATION_6G_SENSOR, "rx_utilization_6ghz"),
                                          (INTER_UTILIZATION_6G_SENSOR, "interference_utilization_6ghz")
            ):

                if not mac in controller.entities[DOMAIN][sensor_type]:
                    sensors.append(OmadaDeviceRadioUtilizationSensor(
                        controller, mac, sensor_type, property))

    if sensors:
        async_add_entities(sensors)


class OmadaDeviceBandwidthSensor(OmadaDevice, SensorEntity):

    DOMAIN = DOMAIN

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfInformation.MEGABYTES

    @property
    def name(self) -> str:
        return f"{super().name} {self.TYPE.title()}"
    
    @callback
    async def options_updated(self):
        if not self._controller.option_device_bandwidth_sensors:
            await self.remove()
        else:
            await super().options_updated()


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


class OmadaDeviceDataRateSensor(OmadaDevice, SensorEntity):

    DOMAIN = DOMAIN

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfDataRate.MEGABYTES_PER_SECOND

    @property
    def name(self) -> str:
        return f"{super().name} {self.TYPE.upper()} Activity"
    
    @callback
    async def options_updated(self):
        if not self._controller.option_device_bandwidth_sensors:
            await self.remove()
        else:
            await super().options_updated()


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


class OmadaDeviceUptimeSensor(OmadaDevice, SensorEntity):

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
    
    @callback
    async def options_updated(self):
        if not self._controller.option_device_statistics_sensors:
            await self.remove()
        else:
            await super().options_updated()


class OmadaDeviceSensor(OmadaDevice, SensorEntity):

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

    @callback
    async def options_updated(self):
        if not self._controller.option_device_statistics_sensors:
            await self.remove()
        else:
            await super().options_updated()


class OmadaDeviceMemUtilSensor(OmadaDeviceSensor):

    TYPE = MEMORY_USAGE_SENSOR
    PROPERTY = "memory"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = PERCENTAGE

    @callback
    async def options_updated(self):
        if not self._controller.option_device_statistics_sensors:
            await self.remove()
        else:
            await super().options_updated()


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

    @callback
    async def options_updated(self):
        if not self._controller.option_device_clients_sensors:
            await self.remove()
        else:
            await super().options_updated()


class OmadaDeviceRadioUtilizationSensor(OmadaDeviceSensor):

    def __init__(self, controller, mac, type, property):
        self.TYPE = type
        self.PROPERTY = property

        super().__init__(controller, mac)

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = PERCENTAGE

    @callback
    async def options_updated(self):
        if not self._controller.option_device_radio_utilization_sensors:
            await self.remove()
        else:
            await super().options_updated()
