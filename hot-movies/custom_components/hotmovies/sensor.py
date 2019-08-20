"""
A component which allows you to parse http://58921.com/ get hot movies

For more details about this component, please refer to the documentation at
https://github.com/aalavender/HotMovies/

"""
import logging
import voluptuous as vol
from datetime import timedelta
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import (PLATFORM_SCHEMA)
from homeassistant.const import (CONF_NAME)
from requests import request
from bs4 import BeautifulSoup

__version__ = '0.1.0'
_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['requests', 'beautifulsoup4']

COMPONENT_REPO = 'https://github.com/aalavender/HotMovies/'
SCAN_INTERVAL = timedelta(hours=8)
ICON = 'mdi:movie-roll'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    add_devices([HotMoviesSensor(hass, config)])

class HotMoviesSensor(Entity):
    def __init__(self, hass, config):
        self.hass = hass
        self._name = config[CONF_NAME]
        self._state = None
        self._entries = []
        self.update()

    def update(self):
        _LOGGER.info("HotMoviesSensor update info from http://58921.com/ ")
        self._entries = []
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36'
        }
        response = request('GET', 'http://58921.com/', headers=header)  # 定义头信息发送请求返回response对象
        response.encoding = 'utf-8'   #不写这句会乱码
        soup = BeautifulSoup(response.text, "lxml")
        trs = soup.select('#front_block_top_day > div > table > tbody > tr')
        self._state = len(trs)
        for tr in trs:
            entryValue = {}
            tds = tr.select('td')
            entryValue["title"] = tds[0].text
            entryValue["day"] = tds[1].text
            entryValue["total"] = tds[2].text
            entryValue["ptime"] = tds[1].get('title')[5:]

            self._entries.append(entryValue)

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return ICON

    @property
    def device_state_attributes(self):
        return {
            'entries': self._entries
        }
