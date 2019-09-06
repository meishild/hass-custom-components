"""Sensor for Siemens Dock devices."""

import logging
import time
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import async_timeout

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import TEMP_CELSIUS, CONF_DISPLAY_OPTIONS
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

# 数据刷新时间
SCAN_INTERVAL = timedelta(seconds=30)

# 外部参数依赖
CONF_SERIAL_NO = "serial_no"

SENSOR_TYPES = {
    'temperature': ['temperature', TEMP_CELSIUS],
    'humidity': ['humidity', '%'],

    'pm2.5': ['pm2.5', 'μg/m³'],
    'pm10': ['pm10', 'μg/m³'],
    'pm1.0': ['pm1.0', 'μg/m³'],
    'hcho': ['hcho', 'ppm'],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_DISPLAY_OPTIONS, default=list(SENSOR_TYPES)): [vol.In(SENSOR_TYPES)],
        vol.Required(CONF_SERIAL_NO): cv.string
    }
)

REQ_URL = "https://server.developmentservice.cn/device/realTimeData"


# 安装方法
async def async_setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """Setup."""
    serial_no = config.get(CONF_SERIAL_NO)
    dev = []
    api = CallAPI(async_create_clientsession(hass), hass.loop, serial_no)
    data = await api.update()

    if 'code' not in data or data['code'] != 200:
        raise PlatformNotReady()
    pid = data['body']['PID']
    for variable in config[CONF_DISPLAY_OPTIONS]:
        unique_id = "sie_%s_%s" % (variable, pid)
        dev.append(SiemensSensor(unique_id, api, variable))

    add_devices_callback(dev, True)


# 通用业务类
class SiemensSensor(Entity):
    def __init__(self, unique_id, api, sensor_types):
        """Initialize."""
        self._unique_id = unique_id
        self._api = api
        self._name = SENSOR_TYPES[sensor_types][0]
        self._unit_of_measurement = SENSOR_TYPES[sensor_types][1]
        self.type = sensor_types
        self._state = None
        self._message_data = {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._unique_id

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._unit_of_measurement

    @property
    def device_state_attributes(self):
        """Return other details about the last message."""
        return self._message_data

    def get_last_message(self, data):
        last_timestamp = data['RT']['timestamp']
        if 'cube' in data:
            last_timestamp = data['cube']['RT']['timestamp']

        local_time = time.localtime(last_timestamp)
        date_format_localtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        res_data = {
            'On': data["STAT"] == 'On',
            'LastUpdate': date_format_localtime
        }

        if 'cube' in data:
            res_data['Battery'] = "%d %%" % ((int)(data['cube']['RT']['Bat']) * 20)
            res_data['Charging'] = data['cube']['RT']['isCharging'] == 1
            res_data['Stable'] = data['cube']['RT']['isStable'] == 1

        return res_data

    # 数据刷新方法
    async def async_update(self):
        """Update data."""
        try:
            data = await self._api.update()
            _LOGGER.debug(data)
            if data is None:
                return
            data = data.get("body", {})
        except Exception as e:
            _LOGGER.debug("Could not get new state", e)
            return

        if data is None:
            return

        if self.type == 'temperature':
            self._state = "%.1f" % (float(data["RT"]["temp"]) / 10)
        if self.type == 'humidity':
            self._state = "%.1f" % (float(data["RT"]["humi"]) / 10)
        if self.type == 'pm2.5' and 'cube' in data:
            self._state = "%.1f" % data['cube']["RT"]["pm2_5"]
        if self.type == 'pm10' and 'cube' in data:
            self._state = "%.1f" % data['cube']["RT"]["pm10"]
        if self.type == 'pm1.0' and 'cube' in data:
            self._state = "%.1f" % data['cube']["RT"]["pm1_0"]
        if self.type == 'hcho' and 'cube' in data:
            self._state = "%d" % data['cube']["RT"]["hcho"]

        self._message_data = self.get_last_message(data)


class CallAPI:
    """Call API."""

    def __init__(self, session, loop, serial_no):
        """Initialize."""
        self.session = session
        self.loop = loop
        self.serial_no = serial_no

    async def update(self):
        """Get json from API endpoint."""
        value = None
        try:
            async with async_timeout.timeout(10, loop=self.loop):
                response = await self.session.post(REQ_URL, json={'serialNo': self.serial_no})
                value = await response.json()
        except Exception as _:
            pass

        return value
