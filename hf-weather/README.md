### 简介 ###
项目fork自https://github.com/cnk700i/ha_modified_components/tree/master/hf_weather
因为我这个整体组装了几个第三方插件，所以做了统一整合，因为做了部分修改，为了防止兼容性问题，只能单向选择没做相互兼容性。

基于和风天气的lovelace天气卡片，主要功能：
- 支持生成多个天气Entity
- 天气数据统一存储
- 天气卡片增加空气质量、小时预报、生活建议、数据更新时间
- 天气卡片更多信息增加生活建议详细数据
- 天气卡片图表增加下雨概率
- 天气卡片使用动态图标
以上原有功能。

- 增加紫外线强度以及位置配置
- 修改地区配置从city改成location，因为紫外线强度需要完整的经纬度，也可以配置local_ip根据ip地址获取经纬度信息。
fix ios、以及safari浏览器无法显示小时的问题
fix 温差过低导致出现小数的问题。


### 使用说明 ###
#### 组件
* 下载文件，hf_weather目录放置在{HA配置目录}/custom_components/下。
* 启用hf_weather组件（[要先在api平台申请key](https://wx.jdcloud.com/market/datas/26/10610)）。

```yaml
# 配置 configuration.yaml
weather:
  - platform: hf_weather
    name: test                  # entity_id，自定义
    location: {{YOUR_LOCATION}} # 支持local_ip,根据ip获取，101.21.221.31，指定ip以及22.25,114.1667指定经纬度三种方式。
    appkey: {{YOUR_API_KEY}}    # api平台申请的key
```

> INFO：重复即可增加多个实体。

* 启用sun组件，用于提供卡片的日出日落数据。。
```yaml
# 配置 configuration.yaml
sun:
```

#### 自定义卡片
> 下载文件，hf_weather-card目录放置在{HA配置目录}/www/custom-lovelace/下。

* lovelace启用天气卡片

```yaml
# 配置lovelace（使用UI的原始编辑器编辑即可）
# 引入自定义卡片hf_weather-card
resources:
  - type: module
    url: /local/custom-lovelace/hf-weather-card/hf-weather-card.js
  - type: module
    url: /local/custom-lovelace/hf-weather-card/hf-weather-more-info.js
# 在view里面的cards节点，增加天气卡片类型
views:
    path: default_view
    title: Home
    cards:
      - type: 'custom:hf-weather-card'                                # card类型
        entity: weather.test                                         # entityid
        mode: daily                                                   # hourly按小时天气预报、daily按天天气预报，不设置则同时显示
        title: 天气                                                   # 标题，不设置则使用entity的friendly_name
        icons: /local/custom-lovelace/hf-weather-card/icons/animated/  # 图标路径，不设置则采用cdn，结尾要有"/"
```
> 所有的配置都集中到了一个实体中如果需要可以通过模版拆分
```yaml
 # 拆分天气
  - platform: template
    sensors:
      weather_current_temp:
        friendly_name: "当前温度"
        unit_of_measurement: '°C'
        value_template: "{{ state_attr('weather.entity_id', 'temperature') }}"
      weather_current_uv:
        friendly_name: "当前紫外线强度"
        value_template: "{{ state_attr('weather.entity_id', 'uv')['uv'] }}"
      weather_current_rain:
        friendly_name: "当前下雨概率"
        unit_of_measurement: '%'
        value_template: "{{ state_attr('weather.entity_id', 'forecast')[0]['probable_precipitation'] }}"
      weather_today_max_temp:
        friendly_name: "今天最高温度"
        unit_of_measurement: '°C'
        value_template: "{{ state_attr('weather.entity_id', 'forecast')[0]['temperature'] }}"
      weather_today_min_temp:
        friendly_name: "今天最低温度"
        unit_of_measurement: '°C'
        value_template: "{{ state_attr('weather.entity_id', 'forecast')[0]['templow'] }}"
```

### 参考 ###
- [和风天气插件组][1]
- [lovelace-weather-card-chart][2]
- [weather-card][3]

[1]: https://bbs.hassbian.com/thread-3971-1-1.html "和风天气插件组(天气预报+生活提示+小时预报+空气质量)"
[2]: https://github.com/sgttrs/lovelace-weather-card-chart "lovelace-weather-card-chart"
[3]: https://github.com/bramkragten/custom-ui/tree/master/weather-card "weather-card"
