"""
Airx空气净化器插件
"""
import logging

import requests
import time
import datetime

from homeassistant.components.fan import (FanEntity)
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = datetime.timedelta(seconds=5)

DEFAULT_NAME = 'airx'

ATTR_PM25 = 'pm25'
ATTR_OUTSIDE_PM25 = 'outside_pm25'
ATTR_FILTER_REMAIN = 'filter_remain'
ATTR_SCREEN_LIGHT = 'screen_light'
ATTR_CHILDREN_LOCK = 'children_lock'

SPEED_OFF = '关闭'
SPEED_AUTO = '自动'
SPEED_SILENT = '静音'
SPEED_LOW = '低'
SPEED_MEDIUM = '中'
SPEED_HIGH = '高'
SPEED_INTOLERABLE = '最高'

SPEED_MAP = {
    1: SPEED_SILENT,
    2: SPEED_LOW,
    3: SPEED_MEDIUM,
    4: SPEED_HIGH,
    5: SPEED_INTOLERABLE,
}
CONTROL_MAP = {
    SPEED_AUTO: [0, 1],
    SPEED_SILENT: [3, 1],
    SPEED_LOW: [3, 2],
    SPEED_MEDIUM: [3, 3],
    SPEED_HIGH: [3, 4],
    SPEED_INTOLERABLE: [3, 5]
}


def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    name = config.get('name') or DEFAULT_NAME
    token = config.get('token')
    user_id = config.get('user_id')
    device_id = config.get('device_id')

    _LOGGER.info('============= airx setup -> name: %s =============', name)
    add_devices_callback([
        AirxFan(hass, name, token, user_id, device_id, AirxController(hass, token, user_id, device_id))
    ])


class AirxController(object):
    lock = None

    def __init__(self, hass, token, user_id, device_id) -> None:
        self._base_data = {
            'userId': user_id,
            'token': token,
            'device_id': device_id,
        }

    def open(self) -> bool:
        _LOGGER.info('============= airx open =============')
        self.lock = time.time()
        try:
            api = 'http://luxcar.com.cn/airx/airx_iot_reportup/web/equipment/DeviceOnOrDown'
            res = requests.post(api, data=dict(self._base_data, **{'standby': 0}))
            json = res.json()
            # _LOGGER.info('open: %s', json)
            if json['success'] is True:
                return True
        except BaseException:
            pass
        return False

    def close(self):
        _LOGGER.info('============= airx close =============')
        self.lock = time.time()
        try:
            api = 'http://luxcar.com.cn/airx/airx_iot_reportup/web/equipment/DeviceOnOrDown'
            res = requests.post(api, data=dict(self._base_data, **{'standby': 1}))
            json = res.json()
            # _LOGGER.info('close: %s', json)
            if json['success'] is True:
                return True
        except BaseException:
            pass
        return False

    def set_speed(self, speed):
        _LOGGER.info('============= airx set speed: %s =============', speed)
        self.lock = time.time()
        try:
            api = 'http://luxcar.com.cn/airx/airx_iot_reportup/web/equipment/DeviceControl'

            set_mode = CONTROL_MAP[speed][0]
            set_speed = CONTROL_MAP[speed][1]

            res = requests.post(
                api,
                data=dict(self._base_data, **{
                    'mode': set_mode,
                    'speed': set_speed
                }))

            json = res.json()
            # _LOGGER.info('set_speed: %s, %s, %s', set_mode, set_speed, json)
            if json['success'] is True:
                return True
        except BaseException:
            pass
        return False

    @property
    def status(self) -> dict:
        _LOGGER.info('============= airx status =============')
        if (self.lock is not None) and (time.time() - self.lock < 5):
            _LOGGER.info('============= airx status return =============')
            return None
        try:
            api = 'http://luxcar.com.cn/airx/airx_iot_reportup/web/equipment/loadDeviceData'
            res = requests.post(api, data=dict(self._base_data))
            json = res.json()
            # _LOGGER.info('status: %s', json)
            if json['success'] is True:
                if json['data']['standby'] == 0:
                    if json['data']['PuriOperationMode'] == 0:
                        speed = SPEED_AUTO
                    else:
                        speed = SPEED_MAP[json['data']['AirSpeed']]
                else:
                    speed = SPEED_OFF
                return {
                    'available': True,
                    'speed': speed,
                    'state_remain': json['data']['FilterRemain'],
                    'state_pm25': json['data']['pm25'],
                    'state_outside_pm25': json['data']['pm25_city'],
                    'state_light': json['data']['Inlight'],
                    'state_lock': json['data']['Childrenlock']
                }
        except BaseException:
            pass
        return {
            'available': False,
            'speed': None,
            'state_remain': None,
            'state_pm25': None,
            'state_outside_pm25': None,
            'state_light': None,
            'state_lock': None
        }


class AirxFan(FanEntity):
    def __init__(self, hass, name: str, token: str, user_id: str, device_id: str, controller) -> None:
        self._hass = hass
        self._available = True
        self._name = name
        self._controller = controller

        self._speed = SPEED_OFF
        self._updatetime = None
        self._state_pm25 = None
        self._state_remain = None
        self._state_outside_pm25 = None
        self._state_light = None
        self._state_lock = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def available(self) -> bool:
        return self._available

    @property
    def should_poll(self):
        return True

    @property
    def speed(self) -> str:
        return self._speed

    @property
    def speed_list(self) -> list:
        return [
            SPEED_OFF, SPEED_AUTO, SPEED_SILENT, SPEED_LOW, SPEED_MEDIUM,
            SPEED_HIGH, SPEED_INTOLERABLE
        ]

    def turn_on(self, speed: str, **kwargs) -> None:
        if speed == SPEED_OFF:
            self.turn_off()
            return
        if speed is None:
            speed = SPEED_AUTO
        if self._speed == SPEED_OFF:
            self._controller.open()
        if self._controller.set_speed(speed) is True:
            self._speed = speed
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs) -> None:
        if self._controller.close() is True:
            self._speed = SPEED_OFF
        self.schedule_update_ha_state()

    @property
    def is_on(self) -> bool:
        return SPEED_OFF != self._speed

    @Throttle(SCAN_INTERVAL)
    def update(self) -> None:

        data = self._controller.status

        if data is None:
            return
        self._available = data['available']
        self._speed = data['speed']
        self._state_remain = data['state_remain']
        self._state_outside_pm25 = data['state_outside_pm25']
        self._state_pm25 = data['state_pm25']
        self._state_light = data['state_light']
        self._state_lock = data['state_lock']

    @property
    def device_state_attributes(self):
        return {
            ATTR_PM25: self._state_pm25,
            ATTR_OUTSIDE_PM25: self._state_outside_pm25,
            ATTR_FILTER_REMAIN: self._state_remain,
            ATTR_SCREEN_LIGHT: self._state_light,
            ATTR_CHILDREN_LOCK: self._state_lock
        }
