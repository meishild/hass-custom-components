import asyncio
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.const import (
    CONF_FORCE_UPDATE, CONF_MONITORED_CONDITIONS, CONF_NAME, CONF_MAC, CONF_FRIENDLY_NAME
)
from bluepy.btle import Scanner, DefaultDelegate
import math

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['bluepy==1.1.4']

DEFAULT_NAME = 'ble_presence'
DEFAULT_FRIENDLY_NAME = '蓝牙定位设备'
ICON = 'mdi:account-multiple'
CONF_ARG_A = 'arg_a'
CONF_ARG_N = 'arg_n'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MAC): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_FRIENDLY_NAME, default=DEFAULT_FRIENDLY_NAME): cv.string,
    vol.Optional(CONF_ARG_A, default=75): cv.positive_int,
    vol.Optional(CONF_ARG_N, default=2.0): vol.Coerce(float),
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the ble_presence sensor."""
    mac = config.get(CONF_MAC)
    if mac is None:
        _LOGGER.error('ble_presence:Pls enter mac!')
    name = config.get(CONF_NAME)
    friendly_name = config.get(CONF_FRIENDLY_NAME)
    arg_a = config.get(CONF_ARG_A)
    arg_n = config.get(CONF_ARG_N)

    dev = [BLEPresenceSensor(hass, name, friendly_name, mac, arg_a, arg_n)]
    async_add_devices(dev, True)


class BLEPresenceSensor(Entity):
    def __init__(self, hass, sensor_name, friendly_name, mac, arg_a, arg_n):

        self._hass = hass
        self.entity_id = async_generate_entity_id(
            'sensor.{}', sensor_name, hass=self._hass)
        self._name = friendly_name
        self._mac = mac
        self._state = None
        self._attributes = {}
        self._arg_a = arg_a
        self._arg_n = arg_n

    class ScanDelegate(DefaultDelegate):
        def __init__(self):
            DefaultDelegate.__init__(self)

        def handleDiscovery(self, dev, isNewDev, isNewData):
            if isNewDev:
                print("Discovered device", dev.addr)
            elif isNewData:
                print("Received new data from", dev.addr)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def unit_of_measurement(self):
        """返回unit_of_measuremeng属性."""
        return 'm'

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return ICON

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def rssi_to_distance(self, rssi):
        distance = math.pow(10, (abs(rssi) - self._arg_a) / (10 * self._arg_n))
        return distance

    @asyncio.coroutine
    def async_update(self):
        scanner = Scanner().withDelegate(self.ScanDelegate())
        devices = scanner.scan(10.0)
        ble_rssi = None
        for dev in devices:
            if dev.addr == self._mac.lower():
                ble_rssi = dev.rssi
        if ble_rssi == None:
            self._state = "未检测到设备"
        else:
            self._state = self.rssi_to_distance(ble_rssi)
            self._attributes['rssi'] = ble_rssi
