"""

"""
import logging
import re
from datetime import datetime, timedelta

import asyncio
import async_timeout
import aiohttp

import voluptuous as vol
from homeassistant.exceptions import PlatformNotReady

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval

from homeassistant.components.weather import (
    WeatherEntity, ATTR_FORECAST_CONDITION, ATTR_FORECAST_TEMP,
    ATTR_FORECAST_TEMP_LOW, ATTR_FORECAST_PRECIPITATION, ATTR_FORECAST_TIME, PLATFORM_SCHEMA)
from homeassistant.const import (ATTR_ATTRIBUTION, TEMP_CELSIUS, CONF_NAME)
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util

__version__ = '0.1.1'
_LOGGER = logging.getLogger(__name__)
REQUIREMENTS = ['requests']
TIME_BETWEEN_UPDATES = timedelta(seconds=1800)

DEFAULT_TIME = dt_util.now()

CONF_LOCATION = "location"
CONF_APPKEY = "appkey"

ATTR_CONDITION_CN = "condition_cn"
ATTR_UPDATE_TIME = "update_time"
ATTR_AQI = "aqi"
ATTR_UV = "uv"
ATTR_HOURLY_FORECAST = "hourly_forecast"
ATTR_SUGGESTION = "suggestion"
ATTR_CUSTOM_UI_MORE_INFO = "custom_ui_more_info"
CONDITION_CLASSES = {
    'sunny': ["晴"],
    'cloudy': ["多云"],
    'partlycloudy': ["少云", "晴间多云", "阴"],
    'windy': ["有风", "微风", "和风", "清风"],
    'windy-variant': ["强风", "疾风", "大风", "烈风"],
    'hurricane': ["飓风", "龙卷风", "热带风暴", "狂暴风", "风暴"],
    'rainy': ["毛毛雨", "小雨", "中雨", "大雨", "阵雨", "极端降雨"],
    'pouring': ["暴雨", "大暴雨", "特大暴雨", "强阵雨"],
    'lightning-rainy': ["雷阵雨", "强雷阵雨"],
    'fog': ["雾", "薄雾"],
    'hail': ["雷阵雨伴有冰雹"],
    'snowy': ["小雪", "中雪", "大雪", "暴雪", "阵雪"],
    'snowy-rainy': ["雨夹雪", "雨雪天气", "阵雨夹雪"],
}
TRANSLATE_SUGGESTION = {
    'air': '空气污染扩散条件指数',
    'drsg': '穿衣指数',
    'uv': '紫外线指数',
    'comf': '舒适度指数',
    'flu': '感冒指数',
    'sport': '运动指数',
    'trav': '旅游指数',
    'cw': '洗车指数',
}

ATTRIBUTION = "来自和风天气的天气数据"

ATTR_FORECAST_PROBABLE_PRECIPITATION = 'probable_precipitation'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_LOCATION): cv.string,
    vol.Required(CONF_APPKEY): cv.string,
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the hefeng weather."""
    _LOGGER.info("setup platform weather.Heweather...")
    name = config.get(CONF_NAME)
    location = config.get(CONF_LOCATION)
    appkey = config.get(CONF_APPKEY)

    is_ip = re.match(r"^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$", location) is not None
    if location == "local_ip" or location is None or is_ip:
        url = "https://api.ip.sb/geoip"
        if is_ip:
            url = url + "/" + location
        import requests
        ip = requests.get(url)
        ip_data = ip.json()

        lat = round(float(ip_data['latitude']), 2)
        lon = round(float(ip_data['longitude']), 2)
        location = "%f,%f" % (lat, lon)

    if "," not in location:
        raise PlatformNotReady("仅支持，ip、经纬度以及local_ip三种配置")

    data = WeatherData(hass, location, appkey)

    yield from data.async_update(dt_util.now())
    async_track_time_interval(hass, data.async_update, TIME_BETWEEN_UPDATES)

    async_add_devices([HeFengWeather(data, name)], True)


class HeFengWeather(WeatherEntity):
    """Representation of a weather condition."""

    def __init__(self, data, object_id):
        """Initialize the  weather."""
        self._name = None
        self._object_id = object_id
        self._condition = None
        self._temperature = None
        self._temperature_unit = None
        self._humidity = None
        self._pressure = None
        self._wind_speed = None
        self._wind_bearing = None
        self._forecast = None

        self._data = data
        self._updatetime = None
        self._aqi = None
        self._uv = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._object_id

    @property
    def registry_name(self):
        """返回实体的friendly_name属性."""
        return '{} {}'.format('和风天气', self._name)

    @property
    def should_poll(self):
        """attention No polling needed for a demo weather condition."""
        return True

    @property
    def temperature(self):
        """Return the temperature."""
        return self._temperature

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._temperature_unit

    @property
    def humidity(self):
        """Return the humidity."""
        return self._humidity

    @property
    def wind_bearing(self):
        """Return the wind speed."""
        return self._wind_bearing

    @property
    def wind_speed(self):
        """Return the wind speed."""
        return self._wind_speed

    @property
    def pressure(self):
        """Return the pressure."""
        return self._pressure

    @property
    def condition(self):
        """Return the weather condition."""
        if self._condition:
            return [k for k, v in CONDITION_CLASSES.items() if self._condition in v][0]
        else:
            return 'unknown'

    @property
    def attribution(self):
        """Return the attribution."""
        return 'Powered by Home Assistant'

    @property
    def device_state_attributes(self):
        """设置其它一些属性值."""
        if self._condition is not None:
            return {
                ATTR_ATTRIBUTION: ATTRIBUTION,
                ATTR_UPDATE_TIME: self._updatetime,
                ATTR_CONDITION_CN: self._condition,
                ATTR_AQI: self._aqi,
                ATTR_HOURLY_FORECAST: self.hourly_forecast,
                ATTR_SUGGESTION: self._suggestion,
                ATTR_UV: self._uv,
                ATTR_CUSTOM_UI_MORE_INFO: "hf-weather-more-info"
            }

    @property
    def forecast(self):
        """Return the forecast."""
        if self._daily_forecast is None:
            return None
        reftime = datetime.now()

        forecast_data = []
        _LOGGER.debug('daily_forecast: %s', self._daily_forecast)
        for entry in self._daily_forecast:
            data_dict = {
                ATTR_FORECAST_CONDITION: entry[0],
                ATTR_FORECAST_TEMP: entry[1],
                ATTR_FORECAST_TEMP_LOW: entry[2],
                ATTR_FORECAST_TIME: entry[3],
                ATTR_FORECAST_PRECIPITATION: entry[4],
                ATTR_FORECAST_PROBABLE_PRECIPITATION: entry[5]
            }
            reftime = reftime + timedelta(days=1)
            forecast_data.append(data_dict)
        # _LOGGER.debug('forecast_data: %s', forecast_data)
        return forecast_data

    @property
    def hourly_forecast(self):
        """Return the forecast."""
        if self._hourly_forecast is None:
            return None
        forecast_data = []
        _LOGGER.debug('hourly_forecast: %s', self._hourly_forecast)
        for entry in self._hourly_forecast:
            data_dict = {
                ATTR_FORECAST_CONDITION: entry[0],
                ATTR_FORECAST_TEMP: entry[1],
                ATTR_FORECAST_TIME: entry[2],
                ATTR_FORECAST_PROBABLE_PRECIPITATION: entry[3]
            }
            forecast_data.append(data_dict)
        # _LOGGER.debug('hourly_forecast_data: %s', forecast_data)
        return forecast_data

    @asyncio.coroutine
    def async_update(self):
        """update函数变成了async_update."""
        self._updatetime = self._data.updatetime
        self._name = self._data.name
        self._condition = self._data.condition
        self._temperature = self._data.temperature
        self._temperature_unit = self._data.temperature_unit
        self._humidity = self._data.humidity
        self._pressure = self._data.pressure
        self._wind_speed = self._data.wind_speed
        self._wind_bearing = self._data.wind_bearing
        self._daily_forecast = self._data.daily_forecast
        self._hourly_forecast = self._data.hourly_forecast
        self._aqi = self._data.aqi
        self._suggestion = self._data.suggestion
        self._uv = self._data.uv
        # _LOGGER.debug("success to update informations")


# 显示紫外线建议
def judge_UV(m):
    if m < 3:
        return (1, "可安全户外运动哦")
    if m >= 3 and m < 5:
        return (2, "涂擦SPF15的防晒霜")
    if m >= 5 and m < 7:
        return (3, "涂擦SPF30的防晒霜")
    if m >= 7 and m < 10:
        return (4, "涂擦SPF30以上的防晒霜，遮阳并躲在阴凉处")
    if m >= 10:
        return (5, "紫外线过于强烈，请勿外出")


class WeatherData(object):
    """天气相关的数据，存储在这个类中."""

    def __init__(self, hass, location, appkey):
        """初始化函数."""
        self._hass = hass
        self._url = "https://way.jd.com/he/freeweather"
        self._uv_url = "https://weather.com/zh-CN/weather/today/l/"
        self._params = {"city": location, "appkey": appkey}
        self._location = location
        self._appkey = appkey
        self._name = None
        self._condition = None
        self._temperature = None
        self._temperature_unit = None
        self._humidity = None
        self._pressure = None
        self._wind_speed = None
        self._wind_bearing = None
        self._forecast = None
        self._updatetime = None
        self._daily_forecast = None
        self._hourly_forecast = None
        self._aqi = None
        self._suggestion = None
        self._uv = None

    @property
    def name(self):
        """地点."""
        return self._name

    @property
    def condition(self):
        """天气情况."""
        return self._condition

    @property
    def temperature(self):
        """温度."""
        return self._temperature

    @property
    def temperature_unit(self):
        """温度单位."""
        return TEMP_CELSIUS

    @property
    def humidity(self):
        """湿度."""
        return self._humidity

    @property
    def pressure(self):
        """气压."""
        return self._pressure

    @property
    def wind_speed(self):
        """风速."""
        return self._wind_speed

    @property
    def wind_bearing(self):
        """风向."""
        return self._wind_bearing

    @property
    def daily_forecast(self):
        """预报."""
        return self._daily_forecast

    @property
    def hourly_forecast(self):
        """小时预报."""
        return self._hourly_forecast

    @property
    def updatetime(self):
        """更新时间."""
        return self._updatetime

    @property
    def aqi(self):
        """空气质量."""
        return self._aqi

    @property
    def suggestion(self):
        """生活建议."""
        return self._suggestion

    @property
    def uv(self):
        return self._uv

    async def async_weather(self, session, url, params):
        with async_timeout.timeout(15, loop=self._hass.loop):
            response = await session.post(url, data=params)
            con_now = await response.json()
            return con_now

    async def async_uv(self, session, url):
        from lxml import etree
        with async_timeout.timeout(15, loop=self._hass.loop):
            uv_response = await session.get(url)
        uv_content = await uv_response.text()
        time_rex = '//*[@id="hero-left-Nowcard-92c6937d-b8c3-4240-b06c-9da9a8b0d22b"]/div/div/section/div[2]/header/p/span[2]'
        cont_rex = '//*[@id="hero-left-Nowcard-92c6937d-b8c3-4240-b06c-9da9a8b0d22b"]/div/div/section/div[2]/div/div[5]/div/span[2]'
        city_rex = '//*[@id="hero-left-Nowcard-92c6937d-b8c3-4240-b06c-9da9a8b0d22b"]/div/div/section/div[2]/header/span/div/h1'
        html = etree.HTML(uv_content)
        time = html.xpath(time_rex)[0].text.split(' ')[0]
        city = html.xpath(city_rex)[0].text.strip()
        uv = html.xpath(cont_rex)[0].text.split("（")[0].strip()
        if uv == '极端':
            uv = 11
        else:
            uv = int(uv)

        level, txt = judge_UV(uv)
        return {
            'uv': uv,
            'last_update_time': time,
            'city': city,
            'level': level,
            'txt': txt
        }

    @asyncio.coroutine
    def async_update(self, now):
        """从远程更新信息."""
        _LOGGER.info("Update from JingdongWangxiang's OpenAPI...")

        """
        # 异步模式的测试代码
        import time
        _LOGGER.info("before time.sleep")
        time.sleep(40)
        _LOGGER.info("after time.sleep and before asyncio.sleep")
        asyncio.sleep(40)
        _LOGGER.info("after asyncio.sleep and before yield from asyncio.sleep")
        yield from asyncio.sleep(40)
        _LOGGER.info("after yield from asyncio.sleep")
        """

        # 通过HTTP访问，获取需要的信息
        # 此处使用了基于aiohttp库的async_get_clientsession
        try:
            session = async_get_clientsession(self._hass)
            weather_data = yield from self.async_weather(session, self._url, self._params)
            uv = yield from self.async_uv(session, self._uv_url + self._location)

        except(asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.error("Error while accessing: %s", self._url)
            return

        # 根据http返回的结果，更新数据
        all_result = weather_data["result"]["HeWeather5"][0]
        self._temperature = float(all_result["now"]["tmp"])
        self._humidity = int(all_result["now"]["hum"])
        self._name = all_result["basic"]["city"]
        self._condition = all_result["now"]["cond"]["txt"]
        self._pressure = int(all_result["now"]["pres"])
        self._wind_speed = float(all_result["now"]["wind"]["spd"])
        self._wind_bearing = float(all_result["now"]["wind"]["deg"])
        self._updatetime = all_result["basic"]["update"]["loc"]
        self._aqi = all_result['aqi']['city']
        self._uv = uv
        self._suggestion = []
        for k, v in all_result["suggestion"].items():
            data = {'title': k, 'title_cn': TRANSLATE_SUGGESTION.get(k, k), 'brf': v.get('brf'), 'txt': v.get('txt')}
            self._suggestion.append(data)

        datemsg = all_result["daily_forecast"]
        forec_cond = []
        for n in range(7):
            for i, j in CONDITION_CLASSES.items():
                if datemsg[n]["cond"]["txt_d"] in j:
                    forec_cond.append(i)
        self._daily_forecast = [
            [forec_cond[0], int(datemsg[0]["tmp"]["max"]), int(datemsg[0]["tmp"]["min"]), datemsg[0]["date"], datemsg[0]["pcpn"],
             datemsg[0]["pop"]],
            [forec_cond[1], int(datemsg[1]["tmp"]["max"]), int(datemsg[1]["tmp"]["min"]), datemsg[1]["date"], datemsg[1]["pcpn"],
             datemsg[1]["pop"]],
            [forec_cond[2], int(datemsg[2]["tmp"]["max"]), int(datemsg[2]["tmp"]["min"]), datemsg[2]["date"], datemsg[2]["pcpn"],
             datemsg[2]["pop"]],
            [forec_cond[3], int(datemsg[3]["tmp"]["max"]), int(datemsg[3]["tmp"]["min"]), datemsg[3]["date"], datemsg[3]["pcpn"],
             datemsg[3]["pop"]],
            [forec_cond[4], int(datemsg[4]["tmp"]["max"]), int(datemsg[4]["tmp"]["min"]), datemsg[4]["date"], datemsg[4]["pcpn"],
             datemsg[4]["pop"]],
            [forec_cond[5], int(datemsg[5]["tmp"]["max"]), int(datemsg[5]["tmp"]["min"]), datemsg[5]["date"], datemsg[5]["pcpn"],
             datemsg[5]["pop"]],
            [forec_cond[6], int(datemsg[6]["tmp"]["max"]), int(datemsg[6]["tmp"]["min"]), datemsg[6]["date"], datemsg[6]["pcpn"],
             datemsg[6]["pop"]]
        ]

        datemsg = all_result["hourly_forecast"]
        forec_cond = []
        for n in range(7):
            for i, j in CONDITION_CLASSES.items():
                if datemsg[n]["cond"]["txt"] in j:
                    forec_cond.append(i)
        self._hourly_forecast = [
            [forec_cond[0], int(datemsg[0]["tmp"]), datemsg[0]["date"], datemsg[0]["pop"]],
            [forec_cond[1], int(datemsg[1]["tmp"]), datemsg[1]["date"], datemsg[1]["pop"]],
            [forec_cond[2], int(datemsg[2]["tmp"]), datemsg[2]["date"], datemsg[2]["pop"]],
            [forec_cond[3], int(datemsg[3]["tmp"]), datemsg[3]["date"], datemsg[3]["pop"]],
            [forec_cond[4], int(datemsg[4]["tmp"]), datemsg[4]["date"], datemsg[4]["pop"]],
            [forec_cond[5], int(datemsg[5]["tmp"]), datemsg[5]["date"], datemsg[5]["pop"]],
            [forec_cond[6], int(datemsg[6]["tmp"]), datemsg[6]["date"], datemsg[6]["pop"]]
        ]

        _LOGGER.info("success to fetch local informations from API")
