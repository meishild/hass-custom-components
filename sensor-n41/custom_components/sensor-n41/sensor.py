#!/usr/bin/env python
# encoding: utf-8
import logging
import datetime

import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant.helpers import config_validation as cv
from homeassistant.const import (CONF_NAME, TEMP_CELSIUS)
from homeassistant.util.dt import now

_LOGGER = logging.getLogger(__name__)
_INTERVAL = 15

SCAN_INTERVAL = datetime.timedelta(seconds=_INTERVAL)

CONF_SK = "sensors"
CONF_DELAY = "delay"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_SK): cv.ensure_list,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the sensor."""
    conf_sensors = config.get(CONF_SK)
    devs = []
    for conf_sensor in conf_sensors:
        id = list(conf_sensor.keys())[0]
        name = conf_sensor[id].get(CONF_NAME)
        sensors = conf_sensor[id].get(CONF_SK)
        delay = conf_sensor[id].get(CONF_DELAY)
        if delay is None or delay < 0:
            delay = 0
        devs.append(Sensor41(hass, id, name, sensors, delay))
    add_devices(devs)


class Sensor41(Entity):
    def __init__(self, hass, unique_id, name, sensors, delay):
        """Initialize the AirCat sensor."""
        self._hass = hass
        self._name = name
        self._unique_id = unique_id
        self._sensors = sensors
        self._state = "off"
        self._delay = delay
        self._last_update_time = None
        self._state_dict = {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def state(self):
        """返回当前的状态."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return other details about the last message."""
        return self._state_dict

    def update(self):
        """Update state."""
        count = 0
        for sensor in self._sensors:
            state = self._hass.states.get(sensor).state
            self._state_dict[sensor] = {"state": state, "last_update": now()}
            if state == 'on':
                self._state = 'on'
            else:
                count = count + 1
        if count == len(self._sensors) and now() - self._last_update_time > self._delay:
            self._state = "off"
